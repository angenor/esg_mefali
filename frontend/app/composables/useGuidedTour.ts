import { ref, readonly, nextTick, createApp, h } from 'vue'
import type { TourState, TourContext, GuidedTourDefinition } from '~/types/guided-tour'
import { tourRegistry, DEFAULT_ENTRY_COUNTDOWN } from '~/lib/guided-tours/registry'
import { loadDriver } from '~/composables/useDriverLoader'
import GuidedTourPopover from '~/components/copilot/GuidedTourPopover.vue'

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
let userInitiatedClose = true
const mountedApps: ReturnType<typeof createApp>[] = []

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

/** Demonte toutes les mini-apps Vue montees dans les popovers */
function unmountAllPopoverApps(): void {
  for (const app of mountedApps) {
    try { app.unmount() } catch { /* deja demonte */ }
  }
  mountedApps.length = 0
}

/** Supprime les elements DOM orphelins laisses par Driver.js */
function cleanupDriverResiduals(): void {
  document.querySelectorAll(
    '.driver-popover, .driver-overlay',
  ).forEach(el => el.remove())

  // Retirer la classe au lieu de supprimer l'element (review #8)
  document.querySelectorAll('.driver-active-element').forEach(el => {
    el.classList.remove('driver-active-element')
  })

  document.querySelectorAll('[data-driver-active-element]').forEach(el => {
    el.removeAttribute('data-driver-active-element')
  })

  document.querySelectorAll('.driver-highlighted-element, .driver-no-animation').forEach(el => {
    el.classList.remove('driver-highlighted-element', 'driver-no-animation')
  })
}

/** Interruption du parcours : cleanup Driver.js, reset UI et state */
function interruptTour(uiStore: ReturnType<typeof import('~/stores/ui').useUiStore>): void {
  unmountAllPopoverApps()
  if (driverInstance) {
    driverInstance.destroy()
    driverInstance = null
  }
  cleanupDriverResiduals()
  uiStore.chatWidgetMinimized = false
  uiStore.guidedTourActive = false
  tourState.value = 'interrupted'
  currentTourId.value = null
  currentStepIndex.value = 0
  setTimeout(() => {
    if (tourState.value === 'interrupted') tourState.value = 'idle'
  }, 500)
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

      // Creer l'instance Driver.js avec popoverRender custom et interruption (Story 5.4)
      let resolveCurrentStep: (() => void) | null = null
      const totalSteps = interpolatedSteps.length

      /** Fabrique une instance Driver.js avec la config partagee */
      function createDriverInstance() {
        return driverModule.driver({
          showProgress: false,
          showButtons: [],
          allowClose: true,
          animate: !uiStore.prefersReducedMotion,
          onDestroyStarted: () => {
            if (cancelled) return // Guard re-entrance (review #1)
            if (userInitiatedClose) {
              cancelTour()
            }
            resolveCurrentStep?.()
            userInitiatedClose = true
          },
        })
      }

      driverInstance = createDriverInstance()

      // ── Traitement entryStep (Story 5.3 — navigation initiale avec decompteur) ──
      const entryStep = definition.entryStep
      let currentRoute = window.location.pathname

      if (entryStep && entryStep.targetRoute !== currentRoute) {
        tourState.value = 'navigating'

        // Highlight du lien sidebar avec popover contenant le decompteur
        const countdownDuration = clampCountdown(entryStep.popover.countdown ?? DEFAULT_ENTRY_COUNTDOWN)

        await new Promise<void>((resolve) => {
          resolveCurrentStep = resolve

          driverInstance!.highlight({
            element: entryStep.selector,
            popover: {
              title: '',
              description: '',
              onPopoverRender: (popover: { wrapper: HTMLElement }) => {
                popover.wrapper.innerHTML = ''
                const container = document.createElement('div')
                popover.wrapper.appendChild(container)

                const app = createApp({
                  render: () => h(GuidedTourPopover, {
                    title: interpolate(entryStep.popover.title, context),
                    description: interpolate(entryStep.popover.description, context),
                    countdown: countdownDuration,
                    currentStep: 0,
                    totalSteps,
                    onClose: () => { cancelTour() },
                    onNext: () => { userInitiatedClose = false; clearCountdownTimer(); resolve() },
                    onCountdownExpired: () => { userInitiatedClose = false; clearCountdownTimer(); resolve() },
                  }),
                })
                app.mount(container)
                mountedApps.push(app)
              },
            },
          })
        })
        resolveCurrentStep = null

        if (cancelled) return

        // Effectuer la navigation
        unmountAllPopoverApps()
        userInitiatedClose = false
        driverInstance?.destroy()
        userInitiatedClose = true
        driverInstance = createDriverInstance()

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

              driverInstance!.highlight({
                element: sidebarSelector,
                popover: {
                  title: '',
                  description: '',
                  onPopoverRender: (popover: { wrapper: HTMLElement }) => {
                    popover.wrapper.innerHTML = ''
                    const container = document.createElement('div')
                    popover.wrapper.appendChild(container)

                    const app = createApp({
                      render: () => h(GuidedTourPopover, {
                        title: step.popover.title,
                        description: step.popover.description,
                        countdown: navCountdown,
                        currentStep: i + 1,
                        totalSteps,
                        onClose: () => { cancelTour() },
                        onNext: () => { userInitiatedClose = false; clearCountdownTimer(); resolve() },
                        onCountdownExpired: () => { userInitiatedClose = false; clearCountdownTimer(); resolve() },
                      }),
                    })
                    app.mount(container)
                    mountedApps.push(app)
                  },
                },
              })
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
          unmountAllPopoverApps()
          userInitiatedClose = false
          if (driverInstance) driverInstance.destroy()
          userInitiatedClose = true
          driverInstance = createDriverInstance()

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

        // Afficher le highlight avec popover custom (Story 5.4)
        unmountAllPopoverApps()
        await new Promise<void>((resolve) => {
          resolveCurrentStep = resolve
          driverInstance!.highlight({
            element: step.selector,
            popover: {
              title: '',
              description: '',
              side: step.popover.side,
              onPopoverRender: (popover: { wrapper: HTMLElement }) => {
                popover.wrapper.innerHTML = ''
                const container = document.createElement('div')
                popover.wrapper.appendChild(container)

                const app = createApp({
                  render: () => h(GuidedTourPopover, {
                    title: step.popover.title,
                    description: step.popover.description,
                    countdown: step.popover.countdown,
                    currentStep: i + 1,
                    totalSteps,
                    onClose: () => { cancelTour() },
                    onNext: () => { userInitiatedClose = false; resolve() },
                    onCountdownExpired: () => { userInitiatedClose = false; resolve() },
                  }),
                })
                app.mount(container)
                mountedApps.push(app)
              },
            },
          })
        })
        resolveCurrentStep = null
      }

      // Finalisation du parcours
      unmountAllPopoverApps()
      if (driverInstance) {
        userInitiatedClose = false
        driverInstance.destroy()
        userInitiatedClose = true
        driverInstance = null
      }
      cleanupDriverResiduals()

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
      unmountAllPopoverApps()
      if (driverInstance) {
        userInitiatedClose = false
        driverInstance.destroy()
        userInitiatedClose = true
        driverInstance = null
      }
      cleanupDriverResiduals()
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
    unmountAllPopoverApps()

    if (driverInstance) {
      userInitiatedClose = false
      driverInstance.destroy()
      userInitiatedClose = true
      driverInstance = null
    }
    cleanupDriverResiduals()

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
