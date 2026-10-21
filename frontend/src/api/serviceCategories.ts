import { apiFetch } from './client'

export interface ServiceCategory {
  id: number
  name: string
  icon: string | null
  expense_category: number | null
  expense_category_name: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

export interface ServiceCategoryDetail extends ServiceCategory {
  invoices_count: number
  invoices_total: string
  last_invoices: {
    id: number
    number: string
    client_name: string
    issue_date: string
    invoice_total: string
    category_amount: string
  }[]
  expenses_count: number
  expenses_total: string
}

export interface ServiceCategoryPayload {
  name: string
  /** Linked expense category id, or null for none. */
  expense_category?: number | null
  /** File to upload, null to clear, undefined to keep the current icon. */
  icon?: File | null
}

function toFormData(payload: ServiceCategoryPayload) {
  const data = new FormData()
  data.set('name', payload.name)
  data.set('expense_category', payload.expense_category ? String(payload.expense_category) : '')
  if (payload.icon instanceof File) data.set('icon', payload.icon)
  else if (payload.icon === null) data.set('icon', '')
  return data
}

export interface PaginatedServiceCategories {
  count: number
  next: string | null
  previous: string | null
  results: ServiceCategory[]
}

export function listServiceCategories(
  params: { search?: string; limit?: number; offset?: number } = {},
) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  query.set('limit', String(params.limit ?? 100))
  query.set('offset', String(params.offset ?? 0))
  const qs = query.toString()
  return apiFetch<PaginatedServiceCategories>(`/api/v1/service-categories/?${qs}`)
}

export function retrieveServiceCategory(id: number) {
  return apiFetch<ServiceCategoryDetail>(`/api/v1/service-categories/${id}/`)
}

export function createServiceCategory(payload: ServiceCategoryPayload) {
  return apiFetch<ServiceCategory>('/api/v1/service-categories/', {
    method: 'POST',
    body: toFormData(payload),
  })
}

export function updateServiceCategory(id: number, payload: ServiceCategoryPayload) {
  return apiFetch<ServiceCategory>(`/api/v1/service-categories/${id}/`, {
    method: 'PUT',
    body: toFormData(payload),
  })
}

export function deleteServiceCategory(id: number) {
  return apiFetch<void>(`/api/v1/service-categories/${id}/`, {
    method: 'DELETE',
  })
}
