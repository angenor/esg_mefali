import { ref, computed, onScopeDispose, getCurrentScope } from 'vue'
import type { Ref, ComputedRef } from 'vue'

const BREAKPOINT = 1024

export interface UseDeviceDetectionReturn {
  isDesktop: Ref<boolean>
  isMobile: ComputedRef<boolean>
}

export function useDeviceDetection(): UseDeviceDetectionReturn {
  const isDesktop = ref(true) // Défaut SSR-safe : desktop

  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    const mql = window.matchMedia(`(min-width: ${BREAKPOINT}px)`)
    isDesktop.value = mql.matches

    const handler = (e: MediaQueryListEvent) => {
      isDesktop.value = e.matches
    }
    mql.addEventListener('change', handler)

    if (getCurrentScope()) {
      onScopeDispose(() => {
        mql.removeEventListener('change', handler)
      })
    } else if (import.meta.dev) {
      console.warn('[useDeviceDetection] Appelé hors d\'un scope Vue — le listener matchMedia ne sera pas nettoyé automatiquement.')
    }
  }

  const isMobile = computed(() => !isDesktop.value)

  return { isDesktop, isMobile }
}
