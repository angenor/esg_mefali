import { ref, readonly, nextTick } from 'vue'
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
let countdownIntervalId: ReturnType<typeof setInterval> | null = null

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

/** Attend qu'un element DOM apparaisse — polling 500ms, timeout configurable */
async function waitForElementExtended(selector: string, timeoutMs: number): Promise<Element | null> {
  const start = Date.now()
  await nextTick()

  while (Date.now() - start < timeoutMs) {
    if (cancelled) return null
    const el = document.querySelector(selector)
    if (el) return el
    await new Promise(r => setTimeout(r, 500))
  }

  return null
}

/** Arrete le timer countdown s'il tourne */
function clearCountdownTimer(): void {
  if (countdownIntervalId !== null) {
    clearInterval(countdownIntervalId)
    countdownIntervalId = null
  }
}

/** Interruption du parcours : cleanup Driver.js, reset UI et state */
function interruptTour(uiStore: ReturnType<typeof import('~/stores/ui').useUiStore>): void {
  if (driverInstance) {
    driverInstance.destroy()
    driverInstance = null
  }
  uiStore.chatWidgetMinimized = false
  uiStore.guidedTourActive = false
  tourState.value = 'interrupted'
  currentTourId.value = null
  currentStepIndex.value = 0
  setTimeout(() => {
    if (tourState.value === 'interrupted') tourState.value = 'idle'
  }, 500)
}

/** Injecte un badge countdown dans le popover Driver.js courant */
function injectCountdownBadge(seconds: number): HTMLSpanElement {
  const badge = document.createElement('span')
  badge.className = 'inline-flex items-center gap-1 rounded-full px-2.5 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm font-semibold tabular-nums'
  badge.setAttribute('data-countdown-badge', '')
  badge.textContent = `${seconds}s`

  const popoverDesc = document.querySelector('.driver-popover-description')
  if (popoverDesc) {
    const container = document.createElement('div')
    container.className = 'mt-2'
    container.appendChild(badge)
    popoverDesc.appendChild(container)
  }

  return badge
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

      // Interpoler les textes des popovers de toutes les etapes
      const interpolatedSteps = definition.steps.map((step) => ({
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

      // ── Traitement entryStep (Story 5.3 — navigation initiale avec decompteur) ──
      const entryStep = definition.entryStep
      let currentRoute = window.location.pathname

      if (entryStep && entryStep.targetRoute !== currentRoute) {
        tourState.value = 'navigating'

        // Highlight du lien sidebar avec popover contenant le decompteur
        const countdownDuration = clampCountdown(entryStep.popover.countdown ?? DEFAULT_ENTRY_COUNTDOWN)

        await new Promise<void>((resolve) => {
          let countdownRemaining = countdownDuration
          resolveCurrentStep = resolve

          driverInstance!.highlight({
            element: entryStep.selector,
            popover: {
              title: interpolate(entryStep.popover.title, context),
              description: interpolate(entryStep.popover.description, context),
              onNextClick: () => {
                clearCountdownTimer()
                resolve()
              },
              onCloseClick: () => {
                clearCountdownTimer()
                resolve()
              },
            },
          })

          // Injecter le badge countdown dans le popover (DOM)
          const badgeEl = injectCountdownBadge(countdownRemaining)

          // Timer du decompteur
          countdownIntervalId = setInterval(() => {
            countdownRemaining--
            badgeEl.textContent = `${countdownRemaining}s`

            if (countdownRemaining <= 0) {
              clearCountdownTimer()
              resolve()
            }
          }, 1000)
        })
        resolveCurrentStep = null

        if (cancelled) return

        // Effectuer la navigation
        driverInstance?.destroy()
        driverInstance = driverModule.driver({
          showProgress: false,
          showButtons: ['next', 'close'],
          animate: !uiStore.prefersReducedMotion,
          onDestroyStarted: () => {
            resolveCurrentStep?.()
          },
        })

        tourState.value = 'waiting_dom'
        await navigateTo(entryStep.targetRoute)
        await nextTick()
        currentRoute = entryStep.targetRoute

        if (cancelled) return

        // Attente DOM : element de la premiere etape (5s puis retry, 10s max)
        const firstStepSelector = interpolatedSteps[0]?.selector
        if (firstStepSelector) {
          const el = await waitForElementExtended(firstStepSelector, 10000)
          if (cancelled) return

          if (!el) {
            const { useChat } = await import('~/composables/useChat')
            const { addSystemMessage } = useChat()
            addSystemMessage('La page n\'a pas pu se charger correctement. Le guidage est interrompu.')
            interruptTour(uiStore)
            return
          }
        }
      }
      // Si entryStep existe mais targetRoute === currentRoute → ignorer (AC7)

      tourState.value = 'highlighting'
      currentStepIndex.value = 0

      // ── Execution sequentielle des etapes (multi-routes — Story 5.3) ──
      for (let i = 0; i < interpolatedSteps.length; i++) {
        if (cancelled) return

        const step = interpolatedSteps[i]!
        currentStepIndex.value = i

        // Verifier si navigation necessaire pour cette etape
        if (step.route && step.route !== currentRoute) {
          tourState.value = 'navigating'

          // Navigation vers la route de l'etape
          const navCountdown = clampCountdown(step.popover.countdown ?? DEFAULT_ENTRY_COUNTDOWN)

          // Highlight du lien sidebar s'il existe, sinon naviguer directement
          const sidebarSelector = `[data-guide-target="sidebar-${step.route.replace(/\//g, '-').replace(/^-/, '')}-link"]`
          const sidebarLink = document.querySelector(sidebarSelector)

          if (sidebarLink) {
            await new Promise<void>((resolve) => {
              resolveCurrentStep = resolve
              let remaining = navCountdown

              driverInstance!.highlight({
                element: sidebarSelector,
                popover: {
                  title: step.popover.title,
                  description: step.popover.description,
                  onNextClick: () => {
                    clearCountdownTimer()
                    resolve()
                  },
                  onCloseClick: () => {
                    clearCountdownTimer()
                    resolve()
                  },
                },
              })

              // Injecter le badge countdown dans le popover sidebar
              const navBadge = injectCountdownBadge(remaining)

              countdownIntervalId = setInterval(() => {
                remaining--
                navBadge.textContent = `${remaining}s`
                if (remaining <= 0) {
                  clearCountdownTimer()
                  resolve()
                }
              }, 1000)
            })
            resolveCurrentStep = null

            if (cancelled) return
          }

          // Naviguer
          tourState.value = 'waiting_dom'
          await navigateTo(step.route)
          await nextTick()
          currentRoute = step.route

          if (cancelled) return

          // Recrer l'instance Driver.js apres navigation
          if (driverInstance) driverInstance.destroy()
          driverInstance = driverModule.driver({
            showProgress: false,
            showButtons: ['next', 'close'],
            animate: !uiStore.prefersReducedMotion,
            onDestroyStarted: () => {
              resolveCurrentStep?.()
            },
          })

          // Attente DOM post-navigation
          const el = await waitForElementExtended(step.selector, 10000)

          if (cancelled) return

          if (!el) {
            const { useChat } = await import('~/composables/useChat')
            const { addSystemMessage } = useChat()
            addSystemMessage('La page n\'a pas pu se charger correctement. Le guidage est interrompu.')
            interruptTour(uiStore)
            return
          }

          tourState.value = 'highlighting'
        } else {
          // Pas de navigation — attendre l'element DOM (retry 3x standard)
          const element = await waitForElement(step.selector)

          if (cancelled) return

          if (!element) {
            const { useChat } = await import('~/composables/useChat')
            const { addSystemMessage } = useChat()
            addSystemMessage('Je n\'ai pas pu pointer cet élément. Passons à la suite.')
            continue
          }
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
      clearCountdownTimer()
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
    clearCountdownTimer()

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
