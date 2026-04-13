import { ref, type Ref, onBeforeUnmount, nextTick } from 'vue'

const FOCUSABLE_SELECTOR =
  'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), ' +
  'a[href], [tabindex]:not([tabindex="-1"])'

export function useFocusTrap(containerRef: Ref<HTMLElement | null>) {
  const isActive = ref(false)

  function getFocusableElements(): HTMLElement[] {
    if (!containerRef.value) return []
    return Array.from(
      containerRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
    )
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (!isActive.value || e.key !== 'Tab') return
    const focusable = getFocusableElements()
    if (focusable.length === 0) return

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }

  function activate() {
    isActive.value = true
    document.addEventListener('keydown', handleKeyDown)
    nextTick(() => {
      const focusable = getFocusableElements()
      if (focusable.length > 0) focusable[0].focus()
    })
  }

  function deactivate() {
    isActive.value = false
    document.removeEventListener('keydown', handleKeyDown)
  }

  onBeforeUnmount(() => deactivate())

  return { activate, deactivate, isActive }
}
