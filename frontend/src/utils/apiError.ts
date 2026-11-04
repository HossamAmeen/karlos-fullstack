import { ApiError } from '@/api/client'

/** Known backend messages -> Arabic explanations shown in popups. */
const KNOWN_MESSAGES: Record<string, string> = {
  'Cannot delete a main category that has categories.':
    'لا يمكن حذف التصنيف الرئيسي لأنه يحتوي على تصنيفات فرعية.',
  'Cannot delete a category that has expenses.':
    'لا يمكن حذف التصنيف لأنه مرتبط بمصروفات.',
  'This category is disabled.': 'هذا التصنيف معطّل ولا يمكن استخدامه.',
  'This main category is disabled.': 'هذا التصنيف الرئيسي معطّل ولا يمكن استخدامه.',
}

function firstMessage(value: unknown): string | null {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.length ? firstMessage(value[0]) : null
  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>
    if ('detail' in record) return firstMessage(record.detail)
    for (const v of Object.values(record)) {
      const found = firstMessage(v)
      if (found) return found
    }
  }
  return null
}

/** Human readable reason for a failed request (never a bare "Request failed: 400"). */
export function apiErrorText(err: unknown, fallback = 'حدث خطأ غير متوقع.'): string {
  if (err instanceof ApiError) {
    const reason = firstMessage(err.body)
    if (reason) return KNOWN_MESSAGES[reason] ?? reason
    if (err.status === 401) return 'انتهت الجلسة، سجّل الدخول مرة أخرى.'
    if (err.status === 403) return 'ليس لديك صلاحية لتنفيذ هذا الإجراء.'
    if (err.status === 404) return 'العنصر غير موجود أو تم حذفه.'
    if (err.status >= 500) return 'حدث خطأ في الخادم، حاول مرة أخرى لاحقًا.'
    return fallback
  }
  return 'تعذر الاتصال بالخادم، تحقق من الاتصال وحاول مرة أخرى.'
}
