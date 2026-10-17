import { apiFetch } from './client'

export type CostMethod = 'fixed' | 'quantity' | 'one_dimension' | 'two_dimensions'

export interface Service {
  id: number
  name: string
  service_category: number
  service_category_name: string
  cost: string
  cost_method: CostMethod
  is_fixed_cost: boolean
  is_additional_service: boolean
  color: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

export interface ServicePayload {
  name: string
  service_category: number
  cost: string
  cost_method: CostMethod
  is_fixed_cost: boolean
  is_additional_service: boolean
  color: string
}

export interface PaginatedServices {
  count: number
  next: string | null
  previous: string | null
  results: Service[]
}

export function listServices(
  params: {
    search?: string
    service_category?: number
    cost_method?: CostMethod
    limit?: number
    offset?: number
  } = {},
) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.service_category != null) {
    query.set('service_category', String(params.service_category))
  }
  if (params.cost_method) query.set('cost_method', params.cost_method)
  query.set('limit', String(params.limit ?? 100))
  query.set('offset', String(params.offset ?? 0))
  const qs = query.toString()
  return apiFetch<PaginatedServices>(`/api/v1/services/?${qs}`)
}

export function createService(payload: ServicePayload) {
  return apiFetch<Service>('/api/v1/services/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateService(id: number, payload: ServicePayload) {
  return apiFetch<Service>(`/api/v1/services/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteService(id: number) {
  return apiFetch<void>(`/api/v1/services/${id}/`, {
    method: 'DELETE',
  })
}
