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

// ── Compteurs de modulation de frequence (FR17 — story 6.4) ──
const GUIDANCE_STATS_KEY = 'esg_mefali_guidance_stats'
// TODO(module 7 — multi-user) : prefixer la cle par user_id quand le systeme
// de sessions sera implemente (cf. deferred-work.md / review 6.4 D3).
// Plancher du countdown multi-pages (FR17) — partage avec la formule adaptative.
const COUNTDOWN_FLOOR = 3
// Plafond des compteurs — au-dela, plancher 3s deja atteint, aucun gain a compter.
const MAX_STATS_CAP = 5
// FR31/NFR18 — retry DOM absent (etape mono-page)
const DOM_RETRY_COUNT = 3
const DOM_RETRY_INTERVAL_MS = 500
// NFR16 — timeouts pour navigation multi-pages
const PAGE_LOAD_SOFT_RETRY_MS = 5000 // fenetre de retry silencieux avec log debug
const PAGE_LOAD_HARD_TIMEOUT_MS = 10000 // timeout dur → interruption + message
const PAGE_LOAD_POLL_INTERVAL_MS = 500 // cadence de polling pendant le chargement de page (decouplee de DOM_RETRY_INTERVAL_MS)
const guidanceRefusalCount = ref<number>(0)
const guidanceAcceptanceCount = ref<number>(0)

interface GuidanceStats {
  refusal_count: number
  acceptance_count: number
}

function loadGuidanceStats(): GuidanceStats {
  if (typeof window === 'undefined') {
    return { refusal_count: 0, acceptance_count: 0 }
  }
  try {
    const raw = window.localStorage.getItem(GUIDANCE_STATS_KEY)
    if (!raw) return { refusal_count: 0, acceptance_count: 0 }
    const parsed: unknown = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') {
      return { refusal_count: 0, acceptance_count: 0 }
    }
    const r = (parsed as Record<string, unknown>).refusal_count
    const a = (parsed as Record<string, unknown>).acceptance_count
    if (typeof r !== 'number' || !Number.isInteger(r) || r < 0) {
      return { refusal_count: 0, acceptance_count: 0 }
    }
    if (typeof a !== 'number' || !Number.isInteger(a) || a < 0) {
      return { refusal_count: 0, acceptance_count: 0 }
    }
    // Defense en profondeur : clamp meme si le JSON contient des valeurs gonflees.
    return {
      refusal_count: Math.min(r, MAX_STATS_CAP),
      acceptance_count: Math.min(a, MAX_STATS_CAP),
    }
  } catch {
    return { refusal_count: 0, acceptance_count: 0 }
  }
}

function persistGuidanceStats(): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(
      GUIDANCE_STATS_KEY,
      JSON.stringify({
        refusal_count: guidanceRefusalCount.value,
        acceptance_count: guidanceAcceptanceCount.value,
      }),
    )
  } catch (err) {
    // localStorage peut throw en mode privacy Safari ou quota depasse —
    // on log sans bloquer le flux.
    // eslint-disable-next-line no-console
    console.warn('[useGuidedTour] persist guidance_stats failed', err)
  }
}

// Initialisation module-level : lecture localStorage une seule fois au chargement
const _initialStats = loadGuidanceStats()
guidanceRefusalCount.value = _initialStats.refusal_count
guidanceAcceptanceCount.value = _initialStats.acceptance_count

// Review 6.4 P9 — synchronisation multi-onglets via `storage` event.
// Quand un autre onglet modifie la cle, on relit pour eviter les lost-updates.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event: StorageEvent) => {
    if (event.key !== GUIDANCE_STATS_KEY) return
    const fresh = loadGuidanceStats()
    guidanceRefusalCount.value = fresh.refusal_count
    guidanceAcceptanceCount.value = fresh.acceptance_count
  })
}

function incrementGuidanceRefusal(): void {
  guidanceRefusalCount.value = Math.min(guidanceRefusalCount.value + 1, MAX_STATS_CAP)
  persistGuidanceStats()
}

function incrementGuidanceAcceptance(): void {
  // Acceptation : +1 acceptance (plafonne) ET reset refusal a 0.
  guidanceAcceptanceCount.value = Math.min(guidanceAcceptanceCount.value + 1, MAX_STATS_CAP)
  guidanceRefusalCount.value = 0
  persistGuidanceStats()
}

function resetGuidanceStats(): void {
  guidanceRefusalCount.value = 0
  guidanceAcceptanceCount.value = 0
  persistGuidanceStats()
}

/**
 * Calcule le countdown effectif en reduisant le countdown original
 * par le nombre d'acceptations, avec un plancher COUNTDOWN_FLOOR (FR17).
 */
function computeEffectiveCountdown(originalCountdown: number): number {
  return Math.max(COUNTDOWN_FLOOR, originalCountdown - guidanceAcceptanceCount.value)
}

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

/** Attend qu'un element DOM apparaisse — 3 tentatives, 500ms d'intervalle (FR31/NFR18) */
async function waitForElement(selector: string): Promise<Element | null> {
  // Garde d'entree : parite avec waitForElementExtended (AC5)
  if (cancelled) return null
  // Premier essai apres nextTick
  await new Promise(r => setTimeout(r, 0))
  if (cancelled) return null
  const el = document.querySelector(selector)
  if (el) return el

  // Retries avec intervalle, cancelled-aware (AC1, AC5)
  for (let i = 0; i < DOM_RETRY_COUNT; i++) {
    if (cancelled) return null
    await new Promise(r => setTimeout(r, DOM_RETRY_INTERVAL_MS))
    if (cancelled) return null
    const found = document.querySelector(selector)
    if (found) return found
  }

  return null
}

/** Attend qu'un element DOM apparaisse — polling PAGE_LOAD_POLL_INTERVAL_MS, timeout configurable (NFR16) */
async function waitForElementExtended(selector: string, timeoutMs: number): Promise<Element | null> {
  const start = Date.now()
  let softLogged = false
  await nextTick()

  while (Date.now() - start < timeoutMs) {
    if (cancelled) return null
    const el = document.querySelector(selector)
    if (el) return el

    // NFR16 — marqueur de soft retry (une seule fois, si on depasse la fenetre soft)
    if (!softLogged && Date.now() - start >= PAGE_LOAD_SOFT_RETRY_MS) {
      // eslint-disable-next-line no-console
      console.debug('[useGuidedTour] soft retry page load', { selector, elapsedMs: Date.now() - start })
      softLogged = true
    }

    await new Promise(r => setTimeout(r, PAGE_LOAD_POLL_INTERVAL_MS))
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
  /**
   * @returns true si le parcours s'est deroule jusqu'a la completion,
   *          false s'il a ete annule, interrompu, ou si tour_id est inconnu.
   *          Review 6.4 P4 : permet au caller de ne crediter une acceptance
   *          qu'en cas de succes reel (pas d'acceptance fantome).
   */
  async function startTour(tourId: string, context?: TourContext): Promise<boolean> {
    // Ignorer si un parcours est deja en cours
    if (tourState.value !== 'idle') return false

    // Valider tour_id dans le registre
    const definition: GuidedTourDefinition | undefined = tourRegistry[tourId as keyof typeof tourRegistry]
    if (!definition) {
      const { useChat } = await import('~/composables/useChat')
      const { addSystemMessage } = useChat()
      addSystemMessage(`Parcours « ${tourId} » introuvable.`)
      return false
    }

    tourState.value = 'loading'
    currentTourId.value = tourId
    cancelled = false

    // Capture acceptance_count au demarrage (FR17 — une seule evaluation,
    // pas de recalcul pendant que l'utilisateur navigue entre etapes)
    const acceptanceSnapshot = guidanceAcceptanceCount.value

    try {
      // Resoudre uiStore AVANT loadDriver : en cas de rejet du loader, le catch global
      // doit disposer d'une reference a jour pour restaurer les flags widget
      // (sinon risque d'ecrire dans un cachedUiStore stale d'un parcours precedent).
      const { useUiStore } = await import('~/stores/ui')
      const uiStore = useUiStore()
      cachedUiStore = uiStore

      // Charger Driver.js via le loader lazy (ADR7)
      const driverModule = await loadDriver()

      // Verifier annulation apres chaque await
      if (cancelled) return false

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
        return false
      }

      // Retraction du widget avant Driver.js (ADR6)
      uiStore.guidedTourActive = true
      uiStore.chatWidgetMinimized = true

      if (uiStore.chatWidgetOpen) {
        await new Promise<void>((resolve) => { onRetractComplete = resolve })
        if (cancelled) return false
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
        // FR17 : reduction adaptative (plancher COUNTDOWN_FLOOR) selon les acceptations anterieures
        const baseCountdown = clampCountdown(entryStep.popover.countdown ?? DEFAULT_ENTRY_COUNTDOWN)
        const countdownDuration = Math.max(COUNTDOWN_FLOOR, baseCountdown - acceptanceSnapshot)

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

        if (cancelled) return false

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

        if (cancelled) return false

        // Attente DOM : element de la premiere etape (5s puis retry, 10s max)
        const firstStepSelector = interpolatedSteps[0]?.selector
        if (firstStepSelector) {
          const el = await waitForElementExtended(firstStepSelector, PAGE_LOAD_HARD_TIMEOUT_MS)
          if (cancelled) return false

          if (!el) {
            const { useChat } = await import('~/composables/useChat')
            const { addSystemMessage } = useChat()
            addSystemMessage('La page met trop de temps à charger. Réessayez plus tard.')
            interruptTour(uiStore)
            return false
          }
        }
      }
      // Si entryStep existe mais targetRoute === currentRoute → ignorer (AC7)

      tourState.value = 'highlighting'
      currentStepIndex.value = 0

      // ── Execution sequentielle des etapes (multi-routes — Story 5.3) ──
      for (let i = 0; i < interpolatedSteps.length; i++) {
        if (cancelled) return false

        const step = interpolatedSteps[i]!
        currentStepIndex.value = i

        // Verifier si navigation necessaire pour cette etape
        if (step.route && step.route !== currentRoute) {
          tourState.value = 'navigating'

          // Navigation vers la route de l'etape
          // FR17 : reduction adaptative (plancher COUNTDOWN_FLOOR) selon les acceptations anterieures
          const baseNavCountdown = clampCountdown(step.popover.countdown ?? DEFAULT_ENTRY_COUNTDOWN)
          const navCountdown = Math.max(COUNTDOWN_FLOOR, baseNavCountdown - acceptanceSnapshot)

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

            if (cancelled) return false
          }

          // Naviguer
          tourState.value = 'waiting_dom'
          await navigateTo(step.route)
          await nextTick()
          currentRoute = step.route

          if (cancelled) return false

          // Recrer l'instance Driver.js apres navigation
          unmountAllPopoverApps()
          userInitiatedClose = false
          if (driverInstance) driverInstance.destroy()
          userInitiatedClose = true
          driverInstance = createDriverInstance()

          // Attente DOM post-navigation
          const el = await waitForElementExtended(step.selector, PAGE_LOAD_HARD_TIMEOUT_MS)

          if (cancelled) return false

          if (!el) {
            const { useChat } = await import('~/composables/useChat')
            const { addSystemMessage } = useChat()
            addSystemMessage('La page met trop de temps à charger. Réessayez plus tard.')
            interruptTour(uiStore)
            return false
          }

          tourState.value = 'highlighting'
        } else {
          // Pas de navigation — attendre l'element DOM (retry 3x standard)
          const element = await waitForElement(step.selector)

          if (cancelled) return false

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
      return true
    } catch (err) {
      // FR31 — log explicite du crash (coherent avec review 6.4 P15, pas de catch muet)
      // eslint-disable-next-line no-console
      console.warn('[useGuidedTour] tour crashed', err)

      // AC4 — message empathique SAUF si l'erreur provient d'un cancelTour user.
      // Snapshot synchrone du flag pour eviter toute race entre check et await import.
      const wasCancelledAtThrow = cancelled
      if (!wasCancelledAtThrow) {
        try {
          const { useChat } = await import('~/composables/useChat')
          // Re-verification post-await : un cancel survenu pendant l'import dynamique
          // doit aussi supprimer le message (AC4 : ne pas spammer apres ESC).
          if (!cancelled) {
            const { addSystemMessage } = useChat()
            addSystemMessage('Le guidage a rencontré un problème. Le chat est toujours disponible.')
          }
        } catch (innerErr) {
          // Si meme l'import de useChat echoue (rare), fallback silencieux —
          // l'utilisateur verra au moins le widget reapparaitre via le cleanup ci-dessous.
          // eslint-disable-next-line no-console
          console.warn('[useGuidedTour] failed to emit crash message', innerErr)
        }
      }

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
      return false
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
    // Compteurs adaptatifs (FR17 — story 6.4)
    guidanceRefusalCount: readonly(guidanceRefusalCount),
    guidanceAcceptanceCount: readonly(guidanceAcceptanceCount),
    incrementGuidanceRefusal,
    incrementGuidanceAcceptance,
    resetGuidanceStats,
    computeEffectiveCountdown,
  }
}
