import { apiFetch } from './client'

export type ExpenseCategory = 'factory' | 'salaries' | 'services'

export interface Expense {
  id: number
  amount: string
  description: string
  expense_date: string
  category: ExpenseCategory
  service_category: number | null
  service_category_name: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

export interface ExpensePayload {
  amount: string
  description: string
  expense_date: string
  category: ExpenseCategory
  service_category: number | null
}

export interface PaginatedExpenses {
  count: number
  next: string | null
  previous: string | null
  results: Expense[]
}

export interface ExpensesSummary {
  total_expenses: number
  total_factory: number
  total_salaries: number
  total_services: number
}

export function listExpenses(
  params: {
    search?: string
    date?: string
    start_date?: string
    end_date?: string
    category?: string
    service_category?: number
    limit?: number
    offset?: number
  } = {},
) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.date) query.set('date', params.date)
  if (params.start_date) query.set('start_date', params.start_date)
  if (params.end_date) query.set('end_date', params.end_date)
  if (params.category) query.set('category', params.category)
  if (params.service_category != null) {
    query.set('service_category', String(params.service_category))
  }
  query.set('limit', String(params.limit ?? 100))
  query.set('offset', String(params.offset ?? 0))
  const qs = query.toString()
  return apiFetch<PaginatedExpenses>(`/api/v1/expenses/?${qs}`)
}

export function getExpensesSummary(
  params: {
    search?: string
    date?: string
    start_date?: string
    end_date?: string
    category?: string
    service_category?: number
  } = {},
) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.date) query.set('date', params.date)
  if (params.start_date) query.set('start_date', params.start_date)
  if (params.end_date) query.set('end_date', params.end_date)
  if (params.category) query.set('category', params.category)
  if (params.service_category != null) {
    query.set('service_category', String(params.service_category))
  }
  const qs = query.toString()
  return apiFetch<ExpensesSummary>(`/api/v1/expenses/summary/?${qs}`)
}

export function createExpense(payload: ExpensePayload) {
  return apiFetch<Expense>('/api/v1/expenses/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateExpense(id: number, payload: ExpensePayload) {
  return apiFetch<Expense>(`/api/v1/expenses/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteExpense(id: number) {
  return apiFetch<void>(`/api/v1/expenses/${id}/`, {
    method: 'DELETE',
  })
}
