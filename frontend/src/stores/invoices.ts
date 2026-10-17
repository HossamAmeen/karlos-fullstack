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

export const useInvoicesStore = defineStore('invoices', () => {
  const items = ref<Invoice[]>([])
  const current = ref<Invoice | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const search = ref('')
  const statusFilter = ref<InvoiceStatus | ''>('')

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await listInvoices({
        search: search.value || undefined,
        status: statusFilter.value || undefined,
      })
      items.value = data.results
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

  async function confirm(invoiceId: number, amountPaid?: string) {
    const invoice = await confirmInvoice(invoiceId, amountPaid)
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

  async function cancel(invoiceId: number) {
    const invoice = await cancelInvoice(invoiceId)
    current.value = invoice
    items.value = items.value.map((i) => (i.id === invoiceId ? invoice : i))
    return invoice
  }

  async function remove(id: number) {
    await deleteInvoice(id)
    items.value = items.value.filter((i) => i.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return {
    items,
    current,
    loading,
    error,
    search,
    statusFilter,
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
    cancel,
    remove,
  }
})
