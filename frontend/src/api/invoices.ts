import { apiFetch } from './client'

export type InvoiceStatus = 'draft' | 'confirmed' | 'cancelled'
export type PaymentStatus = 'unpaid' | 'partial' | 'paid'

export type CostMethod = 'fixed' | 'quantity' | 'one_dimension' | 'two_dimensions'

export interface InvoiceItem {
  id: number
  piece: number
  service: number
  service_name: string
  service_color: string
  cost_method: CostMethod
  unit_price: string
  quantity: string | null
  length: string | null
  width: string | null
  discount_amount: string
  line_subtotal: string
  line_total: string
  position: number
  created_at: string
  updated_at: string
}

export interface InvoicePiece {
  id: number
  length: string | null
  width: string | null
  quantity: string
  notes: string
  piece_subtotal: string
  piece_total: string
  position: number
  items: InvoiceItem[]
  created_at: string
  updated_at: string
}

export interface Invoice {
  id: number
  number: string
  client: number
  client_name: string
  issue_date: string
  status: InvoiceStatus
  discount_amount: string
  notes: string
  subtotal: string
  total: string
  amount_paid: string
  amount_remaining: string
  payment_status: PaymentStatus
  is_settled: boolean
  confirmed_at: string | null
  cancelled_at: string | null
  pieces: InvoicePiece[]
  items: InvoiceItem[]
  created_at: string
  updated_at: string
  deleted_at: string | null
  created_by: number | null
  updated_by: number | null
}

export interface InvoiceCreatePayload {
  client: number
  discount_amount?: string
  notes?: string
  issue_date?: string
}

export interface InvoiceItemPayload {
  service: number
  unit_price?: string
  quantity?: string
  length?: string
  width?: string
  discount_amount?: string
  piece?: number
  piece_quantity?: string
}

export interface InvoicePieceItemPayload {
  service: number
  unit_price?: string
  quantity?: string
  discount_amount?: string
}

export interface InvoicePiecePayload {
  length?: string
  width?: string
  quantity?: string
  notes?: string
  items: InvoicePieceItemPayload[]
}

export interface InvoicePieceUpdatePayload {
  length?: string
  width?: string
  quantity?: string
  notes?: string
}

export interface InvoicePaymentPayload {
  amount: string
  paid_at?: string
  notes?: string
}

export interface PaginatedInvoices {
  count: number
  next: string | null
  previous: string | null
  results: Invoice[]
}

export function listInvoices(
  params: {
    search?: string
    status?: InvoiceStatus
    client?: number
    limit?: number
    offset?: number
  } = {},
) {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.status) query.set('status', params.status)
  if (params.client != null) query.set('client', String(params.client))
  query.set('limit', String(params.limit ?? 100))
  query.set('offset', String(params.offset ?? 0))
  return apiFetch<PaginatedInvoices>(`/api/v1/invoices/?${query}`)
}

export function getInvoice(id: number) {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}/`)
}

export function createInvoice(payload: InvoiceCreatePayload) {
  return apiFetch<Invoice>('/api/v1/invoices/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateInvoice(id: number, payload: Partial<InvoiceCreatePayload>) {
  return apiFetch<Invoice>(`/api/v1/invoices/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteInvoice(id: number) {
  return apiFetch<void>(`/api/v1/invoices/${id}/`, { method: 'DELETE' })
}

export function addInvoiceItem(invoiceId: number, payload: InvoiceItemPayload) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/items/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateInvoiceItem(
  invoiceId: number,
  itemId: number,
  payload: Partial<InvoiceItemPayload>,
) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/items/${itemId}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteInvoiceItem(invoiceId: number, itemId: number) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/items/${itemId}/`, {
    method: 'DELETE',
  })
}

export function addInvoicePiece(invoiceId: number, payload: InvoicePiecePayload) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/pieces/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateInvoicePiece(
  invoiceId: number,
  pieceId: number,
  payload: InvoicePieceUpdatePayload,
) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/pieces/${pieceId}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteInvoicePiece(invoiceId: number, pieceId: number) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/pieces/${pieceId}/`, {
    method: 'DELETE',
  })
}

export function confirmInvoice(invoiceId: number, amountPaid?: string) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/confirm/`, {
    method: 'POST',
    body: JSON.stringify(
      amountPaid != null && amountPaid !== '' ? { amount_paid: amountPaid } : {},
    ),
  })
}

export function payInvoice(invoiceId: number, payload: InvoicePaymentPayload) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/pay/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function cancelInvoice(invoiceId: number) {
  return apiFetch<Invoice>(`/api/v1/invoices/${invoiceId}/cancel/`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}
