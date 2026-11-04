import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  addInvoiceItem,
  addInvoicePiece,
  cancelInvoice,
  confirmInvoice,
  createInvoice,
  deleteInvoice,
  deleteInvoiceItem,
  deleteInvoicePiece,
  getInvoice,
  listInvoices,
  payInvoice,
  printInvoice,
  updateInvoice,
  updateInvoicePiece,
  type Invoice,
  type InvoiceCreatePayload,
  type InvoiceItemPayload,
  type InvoicePaymentPayload,
  type InvoicePiecePayload,
  type InvoicePieceUpdatePayload,
  type InvoiceStatus,
} from '@/api/invoices'
import type { PaymentMethod } from '@/utils/paymentMethods'

export const useInvoicesStore = defineStore('invoices', () => {
  const items = ref<Invoice[]>([])
  const current = ref<Invoice | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const search = ref('')
  const statusFilter = ref<InvoiceStatus | ''>('')
  const dateFrom = ref('')
  const dateTo = ref('')
  const pageSize = 25
  const page = ref(1)
  const totalCount = ref(0)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await listInvoices({
        search: search.value || undefined,
        status: statusFilter.value || undefined,
        issue_date_from: dateFrom.value || undefined,
        issue_date_to: dateTo.value || undefined,
        limit: pageSize,
        offset: (page.value - 1) * pageSize,
      })
      items.value = data.results
      totalCount.value = data.count
      const lastPage = Math.max(1, Math.ceil(data.count / pageSize))
      if (page.value > lastPage) {
        page.value = lastPage
        return fetchAll()
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'فشل تحميل الفواتير'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await getInvoice(id)
      return current.value
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'فشل تحميل الفاتورة'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(payload: InvoiceCreatePayload) {
    const invoice = await createInvoice(payload)
    current.value = invoice
    items.value = [invoice, ...items.value.filter((i) => i.id !== invoice.id)]
    return invoice
  }

  async function updateHeader(id: number, payload: Partial<InvoiceCreatePayload>) {
    const invoice = await updateInvoice(id, payload)
    current.value = invoice
    items.value = items.value.map((i) => (i.id === id ? invoice : i))
    return invoice
  }

  async function addItem(invoiceId: number, payload: InvoiceItemPayload) {
    const invoice = await addInvoiceItem(invoiceId, payload)
    current.value = invoice
    return invoice
  }

  async function removeItem(invoiceId: number, itemId: number) {
    const invoice = await deleteInvoiceItem(invoiceId, itemId)
    current.value = invoice
    return invoice
  }

  async function addPiece(invoiceId: number, payload: InvoicePiecePayload) {
    const invoice = await addInvoicePiece(invoiceId, payload)
    current.value = invoice
    return invoice
  }

  async function updatePiece(
    invoiceId: number,
    pieceId: number,
    payload: InvoicePieceUpdatePayload,
  ) {
    const invoice = await updateInvoicePiece(invoiceId, pieceId, payload)
    current.value = invoice
    return invoice
  }

  async function removePiece(invoiceId: number, pieceId: number) {
    const invoice = await deleteInvoicePiece(invoiceId, pieceId)
    current.value = invoice
    return invoice
  }

  async function confirm(invoiceId: number, amountPaid?: string, method?: PaymentMethod) {
    const invoice = await confirmInvoice(invoiceId, amountPaid, method)
    current.value = invoice
    items.value = items.value.map((i) => (i.id === invoiceId ? invoice : i))
    return invoice
  }

  async function pay(invoiceId: number, payload: InvoicePaymentPayload) {
    const invoice = await payInvoice(invoiceId, payload)
    current.value = invoice
    items.value = items.value.map((i) => (i.id === invoiceId ? invoice : i))
    return invoice
  }

  async function markPrinted(invoiceId: number) {
    const invoice = await printInvoice(invoiceId)
    current.value = invoice
    items.value = items.value.map((i) => (i.id === invoiceId ? invoice : i))
    return invoice
  }

  async function cancel(invoiceId: number) {
    const invoice = await cancelInvoice(invoiceId)
    current.value = invoice
    items.value = items.value.map((i) => (i.id === invoiceId ? invoice : i))
    return invoice
  }

  async function remove(id: number) {
    await deleteInvoice(id)
    items.value = items.value.filter((i) => i.id !== id)
    totalCount.value = Math.max(0, totalCount.value - 1)
    if (current.value?.id === id) current.value = null
  }

  return {
    items,
    current,
    loading,
    error,
    search,
    statusFilter,
    dateFrom,
    dateTo,
    page,
    pageSize,
    totalCount,
    fetchAll,
    fetchOne,
    create,
    updateHeader,
    addItem,
    removeItem,
    addPiece,
    updatePiece,
    removePiece,
    confirm,
    pay,
    markPrinted,
    cancel,
    remove,
  }
})
