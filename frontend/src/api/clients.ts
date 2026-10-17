import { apiFetch } from './client'

export interface Client {
  id: number
  name: string
  phone: string
  email: string
  address: string
  note: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

export interface ClientPayload {
  name: string
  phone: string
  email?: string
  address?: string
  note?: string
}

export interface PaginatedClients {
  count: number
  next: string | null
  previous: string | null
  results: Client[]
}

export type PaymentStatus = 'unpaid' | 'partial' | 'paid'

export interface ClientStatementInvoice {
  id: number
  number: string
  issue_date: string
  status: 'confirmed' | 'cancelled'
  total: string
  amount_paid: string
  amount_remaining: string
  payment_status: PaymentStatus
}

export interface ClientStatementDeposit {
  id: number
  amount: string
  paid_at: string
  notes: string
  invoice: number | null
  invoice_number: string | null
  created_at: string
}

export interface ClientStatement {
  client: Client
  total_charged: string
  total_deposits: string
  balance_due: string
  invoices: ClientStatementInvoice[]
  deposits: ClientStatementDeposit[]
}

export interface ClientDepositPayload {
  amount: string
  paid_at?: string
  notes?: string
}

export function listClients(params: { search?: string; limit?: number; offset?: number } = {}) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  query.set('limit', String(params.limit ?? 100))
  query.set('offset', String(params.offset ?? 0))
  const qs = query.toString()
  return apiFetch<PaginatedClients>(`/api/v1/clients/?${qs}`)
}

export function createClient(payload: ClientPayload) {
  return apiFetch<Client>('/api/v1/clients/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateClient(id: number, payload: ClientPayload) {
  return apiFetch<Client>(`/api/v1/clients/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteClient(id: number) {
  return apiFetch<void>(`/api/v1/clients/${id}/`, {
    method: 'DELETE',
  })
}

export function getClientStatement(id: number) {
  return apiFetch<ClientStatement>(`/api/v1/clients/${id}/statement/`)
}

export function createClientDeposit(id: number, payload: ClientDepositPayload) {
  return apiFetch<ClientStatement>(`/api/v1/clients/${id}/deposits/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
