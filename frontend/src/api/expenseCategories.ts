import { apiFetch } from './client'

interface Audit {
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ExpenseMainCategory extends Audit {
  id: number
  name: string
  categories_count: number
}

export interface ExpenseCategory extends Audit {
  id: number
  main_category: number
  main_category_name: string
  name: string
}

export interface ExpenseMainCategoryPayload {
  name: string
}

export interface ExpenseCategoryPayload {
  main_category: number
  name: string
}

function listQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  return query.toString()
}

function crud<T, P>(path: string) {
  return {
    list: (params: Record<string, string | number | undefined> = {}) =>
      apiFetch<Paginated<T>>(
        `${path}/?${listQuery({ limit: 200, offset: 0, ...params })}`,
      ),
    create: (payload: P) =>
      apiFetch<T>(`${path}/`, { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: P) =>
      apiFetch<T>(`${path}/${id}/`, { method: 'PUT', body: JSON.stringify(payload) }),
    remove: (id: number) => apiFetch<void>(`${path}/${id}/`, { method: 'DELETE' }),
  }
}

export const expenseMainCategoriesApi = crud<
  ExpenseMainCategory,
  ExpenseMainCategoryPayload
>('/api/v1/expense-main-categories')

export const expenseCategoriesApi = crud<ExpenseCategory, ExpenseCategoryPayload>(
  '/api/v1/expense-categories',
)
