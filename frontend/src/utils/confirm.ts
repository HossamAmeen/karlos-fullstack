import { reactive } from 'vue'

export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  /** `danger` (default) paints the confirm button red. */
  tone?: 'danger' | 'default'
}

interface State extends Required<Omit<ConfirmOptions, 'message'>> {
  open: boolean
  message: string
  resolve: ((ok: boolean) => void) | null
}

export const confirmState = reactive<State>({
  open: false,
  title: '',
  message: '',
  confirmText: 'تأكيد',
  cancelText: 'إلغاء',
  tone: 'danger',
  resolve: null,
})

/** Promise-based replacement for window.confirm(). */
export function askConfirm(options: ConfirmOptions): Promise<boolean> {
  confirmState.resolve?.(false)
  Object.assign(confirmState, {
    title: 'تأكيد الإجراء',
    confirmText: 'تأكيد',
    cancelText: 'إلغاء',
    tone: 'danger',
    ...options,
    open: true,
  })
  return new Promise((resolve) => {
    confirmState.resolve = resolve
  })
}

export function settleConfirm(ok: boolean) {
  const resolve = confirmState.resolve
  confirmState.open = false
  confirmState.resolve = null
  resolve?.(ok)
}
