import { ref } from 'vue'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

const toasts = ref<Toast[]>([])

export function useToast() {
  function show(message: string, type: Toast['type'] = 'info', duration = 4000) {
    const id = crypto.randomUUID()
    const toast: Toast = { id, type, message }
    toasts.value = [...toasts.value, toast]

    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
  }

  function dismiss(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function success(message: string) {
    show(message, 'success')
  }

  function error(message: string) {
    show(message, 'error', 6000)
  }

  function info(message: string) {
    show(message, 'info')
  }

  return {
    toasts,
    show,
    dismiss,
    success,
    error,
    info,
  }
}
