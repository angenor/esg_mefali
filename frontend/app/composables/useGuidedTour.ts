import { ref, readonly } from 'vue'
import type { TourState, TourContext, GuidedTourDefinition } from '~/types/guided-tour'
import { tourRegistry, DEFAULT_ENTRY_COUNTDOWN } from '~/lib/guided-tours/registry'
import { loadDriver } from '~/composables/useDriverLoader'

// Sécurité : ce module-level state ne doit jamais s'exécuter côté serveur
if (import.meta.server) throw new Error('useGuidedTour is client-only')

// ── Module-level state (singleton cross-routes — ADR3) ──
const tourState = ref<TourState>('idle')
const currentTourId = ref<string | null>(null)
const currentStepIndex = ref(0)

let driverInstance: ReturnType<typeof import('driver.js').driver> | null = null
let cancelled = false
let cachedUiStore: ReturnType<typeof import('~/stores/ui').useUiStore> | null = null

// ── Synchronisation GSAP → Driver.js (Story 5.2, ADR6) ──
let onRetractComplete: (() => void) | null = null

/** Appele par FloatingChatWidget quand la retraction GSAP est terminee */
export function notifyRetractComplete(): void {
  onRetractComplete?.()
  onRetractComplete = null
}

/** Remplace les placeholders {{key}} par les valeurs du contexte (cle manquante → '') */
function interpolate(text: string, context: TourContext = {}): string {
  return text.replace(/\{\{(\w+)\}\}/g, (_, key) => String(context[key] ?? ''))
}

/** Clamp countdown : min 1 seconde, fallback DEFAULT_ENTRY_COUNTDOWN si non-fini */
function clampCountdown(value: unknown): number {
  const num = Number(value)
  if (!Number.isFinite(num)) return DEFAULT_ENTRY_COUNTDOWN
  if (num < 1) return 1
  return num
}

/** Attend qu'un element DOM apparaisse — 3 tentatives, 500ms d'intervalle */
async function waitForElement(selector: string): Promise<Element | null> {
  // Premier essai apres nextTick
  await new Promise(r => setTimeout(r, 0))
  const el = document.querySelector(selector)
  if (el) return el

  // 3 retries avec 500ms d'intervalle
  for (let i = 0; i < 3; i++) {
    await new Promise(r => setTimeout(r, 500))
    const found = document.querySelector(selector)
    if (found) return found
  }

  return null
}

export function useGuidedTour() {
  async function startTour(tourId: string, context?: TourContext): Promise<void> {
    // Ignorer si un parcours est deja en cours
    if (tourState.value !== 'idle') return

    // Valider tour_id dans le registre
    const definition: GuidedTourDefinition | undefined = tourRegistry[tourId as keyof typeof tourRegistry]
    if (!definition) {
      const { useChat } = await import('~/composables/useChat')
      const { addSystemMessage } = useChat()
      addSystemMessage(`Parcours « ${tourId} » introuvable.`)
      return
    }

    tourState.value = 'loading'
    currentTourId.value = tourId
    cancelled = false

    try {
      // Charger Driver.js via le loader lazy (ADR7)
      const driverModule = await loadDriver()

      // Verifier annulation apres chaque await
      if (cancelled) return

      // Obtenir la route courante
      const currentRoute = window.location.pathname

      // Resoudre les etapes mono-page (route absente ou === currentRoute)
      const monoPageSteps = definition.steps.filter(
        (step) => !step.route || step.route === currentRoute,
      )

      // Interpoler les textes des popovers
      const interpolatedSteps = monoPageSteps.map((step) => ({
        ...step,
        popover: {
          ...step.popover,
          title: interpolate(step.popover.title, context),
          description: interpolate(step.popover.description, context),
          countdown: step.popover.countdown !== undefined
            ? clampCountdown(step.popover.countdown)
            : step.popover.countdown,
        },
      }))

      if (interpolatedSteps.length === 0) {
        tourState.value = 'idle'
        currentTourId.value = null
        return
      }

      // Gerer prefers-reduced-motion (NFR14) + retraction widget (Story 5.2)
      const { useUiStore } = await import('~/stores/ui')
      const uiStore = useUiStore()
      cachedUiStore = uiStore

      // Retraction du widget avant Driver.js (ADR6)
      uiStore.guidedTourActive = true
      uiStore.chatWidgetMinimized = true

      if (uiStore.chatWidgetOpen) {
        await new Promise<void>((resolve) => { onRetractComplete = resolve })
        if (cancelled) return
      }

      // Creer l'instance Driver.js avec onDestroyStarted dans la config initiale
      let resolveCurrentStep: (() => void) | null = null
      driverInstance = driverModule.driver({
        showProgress: false,
        showButtons: ['next', 'close'],
        animate: !uiStore.prefersReducedMotion,
        onDestroyStarted: () => {
          resolveCurrentStep?.()
        },
      })

      tourState.value = 'highlighting'
      currentStepIndex.value = 0

      // Execution sequentielle des etapes
      for (let i = 0; i < interpolatedSteps.length; i++) {
        if (cancelled) return

        const step = interpolatedSteps[i]!
        currentStepIndex.value = i

        // Attendre que l'element DOM soit present (retry 3x)
        const element = await waitForElement(step.selector)

        if (cancelled) return

        if (!element) {
          // Element non trouve apres 3 tentatives — skip + message systeme
          const { useChat } = await import('~/composables/useChat')
          const { addSystemMessage } = useChat()
          addSystemMessage('Je n\'ai pas pu pointer cet élément. Passons à la suite.')
          continue
        }

        // Afficher le highlight
        await new Promise<void>((resolve) => {
          resolveCurrentStep = resolve
          driverInstance!.highlight({
            element: step.selector,
            popover: {
              title: step.popover.title,
              description: step.popover.description,
              side: step.popover.side,
              onNextClick: () => {
                resolve()
              },
              onCloseClick: () => {
                resolve()
              },
            },
          })
        })
        resolveCurrentStep = null
      }

      // Finalisation du parcours
      if (driverInstance) {
        driverInstance.destroy()
        driverInstance = null
      }

      // Reapparition du widget (Story 5.2)
      uiStore.chatWidgetMinimized = false
      uiStore.guidedTourActive = false

      tourState.value = 'complete'
      currentTourId.value = null
      currentStepIndex.value = 0

      // Retour a idle apres delai
      setTimeout(() => {
        if (tourState.value === 'complete') {
          tourState.value = 'idle'
        }
      }, 1000)
    } catch {
      // Reset d'etat en cas d'erreur (loadDriver rejection, highlight throw, etc.)
      if (driverInstance) {
        driverInstance.destroy()
        driverInstance = null
      }
      // Reset flags widget (Story 5.2)
      if (cachedUiStore) {
        cachedUiStore.chatWidgetMinimized = false
        cachedUiStore.guidedTourActive = false
      }
      // Resoudre la promesse de retraction si en attente (evite deadlock F2)
      onRetractComplete?.()
      onRetractComplete = null
      tourState.value = 'idle'
      currentTourId.value = null
      currentStepIndex.value = 0
    }
  }

  function cancelTour(): void {
    if (tourState.value === 'idle' || tourState.value === 'complete') return

    cancelled = true

    if (driverInstance) {
      driverInstance.destroy()
      driverInstance = null
    }

    // Reset flags widget (Story 5.2)
    if (cachedUiStore) {
      cachedUiStore.chatWidgetMinimized = false
      cachedUiStore.guidedTourActive = false
    }
    // Resoudre la promesse de retraction AVANT de la nullifier (evite deadlock F2)
    onRetractComplete?.()
    onRetractComplete = null

    tourState.value = 'interrupted'
    currentTourId.value = null
    currentStepIndex.value = 0

    setTimeout(() => {
      if (tourState.value === 'interrupted') {
        tourState.value = 'idle'
      }
    }, 500)
  }

  return {
    startTour,
    cancelTour,
    tourState: readonly(tourState),
  }
}
