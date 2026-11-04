import type { PaymentMethod } from '@/utils/paymentMethods'

import { apiFetch } from './client'

export interface PaymentRow {
  id: number
  client: number
  client_name: string
  invoice: number | null
  invoice_number: string | null
  amount: string
  method: PaymentMethod
  paid_at: string
  notes: string
  created_at: string
}

export interface PaginatedPayments {
  count: number
  next: string | null
  previous: string | null
  results: PaymentRow[]
}

export interface PaymentsSummary {
  total_payments: string | number
  count: number
  by_method: { method: PaymentMethod; total: string | number; count: number }[]
}

export interface PaymentFilters {
  client?: number
  start_date?: string
  end_date?: string
  method?: PaymentMethod
  search?: string
}

function filtersQuery(params: PaymentFilters) {
  const query = new URLSearchParams()
  if (params.client != null) query.set('client', String(params.client))
  if (params.start_date) query.set('start_date', params.start_date)
  if (params.end_date) query.set('end_date', params.end_date)
  if (params.method) query.set('method', params.method)
  if (params.search) query.set('search', params.search)
  return query
}

export function listPayments(params: PaymentFilters & { limit?: number; offset?: number } = {}) {
  const query = filtersQuery(params)
  query.set('limit', String(params.limit ?? 25))
  query.set('offset', String(params.offset ?? 0))
  return apiFetch<PaginatedPayments>(`/api/v1/payments/?${query}`)
}

export function getPaymentsSummary(params: PaymentFilters = {}) {
  return apiFetch<PaymentsSummary>(`/api/v1/payments/summary/?${filtersQuery(params)}`)
}
