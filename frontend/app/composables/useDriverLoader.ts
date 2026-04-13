/**
 * Utilitaire de chargement lazy de Driver.js.
 * Cache module-level : un seul import() dynamique, reutilise ensuite.
 * Sera consomme par useGuidedTour.ts (Story 5.1).
 */

let driverModule: typeof import('driver.js') | null = null
let inflight: Promise<typeof import('driver.js')> | null = null

/**
 * Effectue l'import dynamique une seule fois.
 * Toute tentative concurrente (prefetch + loadDriver) reutilise la meme promesse.
 */
function importOnce(): Promise<typeof import('driver.js')> {
  if (!inflight) {
    inflight = import('driver.js').then((m) => {
      driverModule = m
      return m
    }).catch((err) => {
      inflight = null
      throw err
    })
  }
  return inflight
}

/**
 * Pre-charge Driver.js en arriere-plan via requestIdleCallback.
 * Appele dans FloatingChatWidget.onMounted().
 * Sur connexions rapides : le module est deja en cache quand le premier guidage arrive.
 * Sur connexions lentes : loadDriver() attendra le chargement (budget 500ms — NFR2).
 */
export function prefetchDriverJs(): void {
  if (driverModule) return

  const callback = () => {
    importOnce().catch(() => {
      // Silencieux en prefetch — loadDriver() retentera si besoin
    })
  }

  if (typeof requestIdleCallback === 'function') {
    requestIdleCallback(callback)
  } else {
    // Fallback pour Safari < 17 qui ne supporte pas requestIdleCallback
    setTimeout(callback, 200)
  }
}

/**
 * Charge Driver.js et retourne le module.
 * Si deja en cache (via prefetch ou appel precedent), retour immediat.
 */
export async function loadDriver(): Promise<typeof import('driver.js')> {
  if (driverModule) return driverModule
  return importOnce()
}
