import { apiFetch } from './client'

export interface Expense {
  id: number
  amount: string
  description: string
  expense_date: string
  category: number
  category_name: string
  main_category: number
  main_category_name: string
  client: number | null
  client_name: string | null
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
  category: number
  client: number | null
}

export interface PaginatedExpenses {
  count: number
  next: string | null
  previous: string | null
  results: Expense[]
}

export interface ExpensesSummary {
  total_expenses: number
  by_main_category: {
    main_category: number
    main_category_name: string
    total: number
  }[]
}

export interface ExpenseFilters {
  search?: string
  date?: string
  start_date?: string
  end_date?: string
  main_category?: number
  category?: number
  client?: number
}

function filtersQuery(params: ExpenseFilters) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.date) query.set('date', params.date)
  if (params.start_date) query.set('start_date', params.start_date)
  if (params.end_date) query.set('end_date', params.end_date)
  if (params.main_category != null) query.set('main_category', String(params.main_category))
  if (params.category != null) query.set('category', String(params.category))
  if (params.client != null) query.set('client', String(params.client))
  return query
}

export function listExpenses(
  params: ExpenseFilters & { limit?: number; offset?: number } = {},
) {
  const query = filtersQuery(params)
  query.set('limit', String(params.limit ?? 100))
  query.set('offset', String(params.offset ?? 0))
  return apiFetch<PaginatedExpenses>(`/api/v1/expenses/?${query.toString()}`)
}

export function getExpensesSummary(params: ExpenseFilters = {}) {
  return apiFetch<ExpensesSummary>(
    `/api/v1/expenses/summary/?${filtersQuery(params).toString()}`,
  )
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
