import { apiFetch } from './client'

export interface ServiceCategory {
  id: number
  name: string
  icon: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

export interface ServiceCategoryPayload {
  name: string
  /** File to upload, null to clear, undefined to keep the current icon. */
  icon?: File | null
}

function toFormData(payload: ServiceCategoryPayload) {
  const data = new FormData()
  data.set('name', payload.name)
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
