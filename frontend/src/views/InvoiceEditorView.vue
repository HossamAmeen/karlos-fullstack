<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { CostMethod, InvoicePieceItemPayload } from '@/api/invoices'
import type { Service } from '@/api/services'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import { useAuthStore } from '@/stores/auth'
import { useClientsStore } from '@/stores/clients'
import { useInvoicesStore } from '@/stores/invoices'
import { useServiceCategoriesStore } from '@/stores/serviceCategories'
import { useServicesStore } from '@/stores/services'
import { applyDiscount, computeLineSubtotal, roundMoney } from '@/utils/pricing'

interface DraftService {
  key: number
  serviceId: number
  serviceName: string
  serviceColor: string
  costMethod: CostMethod
  unitPrice: string
  quantity: string
  discountAmount: string
}

const props = defineProps<{ id?: string }>()

const auth = useAuthStore()
const invoices = useInvoicesStore()
const clients = useClientsStore()
const categories = useServiceCategoriesStore()
const services = useServicesStore()
const router = useRouter()
const route = useRoute()

const headerError = ref<string | null>(null)
const itemError = ref<string | null>(null)
const extraError = ref<string | null>(null)
const savingHeader = ref(false)
const savingItem = ref(false)
const acting = ref(false)
const confirmMode = ref<'completed' | 'without_paid' | 'partial'>('completed')
const payAmount = ref('')
const payNotes = ref('')
const payError = ref<string | null>(null)
const extraPieceId = ref<number | null>(null)
let draftKey = 1

const header = reactive({
  client: '' as string | number,
  discount_amount: '0',
  notes: '',
  issue_date: new Date().toISOString().slice(0, 10),
})

const pieceForm = reactive({
  length: '',
  width: '',
  quantity: '1',
})

const itemForm = reactive({
  category: '' as string | number,
  service: '' as string | number,
  unit_price: '',
  total_price: '',
  quantity: '',
  discount_amount: '0',
})

const extraForm = reactive({
  category: '' as string | number,
  service: '' as string | number,
  unit_price: '',
  total_price: '',
  quantity: '',
  discount_amount: '0',
  length: '',
  width: '',
})

const draftServices = ref<DraftService[]>([])

const invoice = computed(() => invoices.current)
const isNew = computed(() => !props.id && !invoice.value?.id)
const editable = computed(() => isNew.value || !invoice.value || invoice.value.status === 'draft')
const invoicePieces = computed(() => invoice.value?.pieces ?? [])
const invoiceItems = computed(() => invoice.value?.items ?? [])
const legacyInvoiceItems = computed(() =>
  invoicePieces.value.length ? [] : invoiceItems.value,
)
const hasPieces = computed(
  () => invoicePieces.value.length > 0 || invoiceItems.value.length > 0,
)

const availableCategories = computed(() =>
  categories.items.filter((category) =>
    services.items.some((service) => service.service_category === category.id),
  ),
)

const filteredServices = computed(() => {
  if (itemForm.category === '' || itemForm.category == null) return services.items
  return services.items.filter((s) => s.service_category === Number(itemForm.category))
})

const extraFilteredServices = computed(() => {
  if (extraForm.category === '' || extraForm.category == null) return services.items
  return services.items.filter((s) => s.service_category === Number(extraForm.category))
})

const selectedService = computed(() =>
  services.items.find((s) => s.id === Number(itemForm.service)),
)

const extraSelectedService = computed(() =>
  services.items.find((s) => s.id === Number(extraForm.service)),
)

const extraPiece = computed(() =>
  invoice.value?.pieces.find((p) => p.id === extraPieceId.value),
)

const extraPieceHasDims = computed(() => {
  const piece = extraPiece.value
  return Boolean(piece && piece.length != null && piece.width != null)
})

const showExtraDimensionInputs = computed(() => {
  const service = extraSelectedService.value
  return Boolean(service && needsDimensions(service.cost_method) && !extraPieceHasDims.value)
})

const showExtraTwoDimensions = computed(() => {
  const service = extraSelectedService.value
  return Boolean(service && needsTwoDimensions(service.cost_method) && !extraPieceHasDims.value)
})

const costMethodLabels: Record<string, string> = {
  fixed: 'ثابت',
  quantity: 'كمية',
  one_dimension: 'بعد واحد (x×x)',
  two_dimensions: 'بعدين ((x+y)×2)',
  perimeter: 'بعدين ((x+y)×2)',
  area: 'بعد واحد (x×x)',
}

const statusLabels = {
  draft: 'مسودة',
  confirmed: 'مؤكدة',
  cancelled: 'ملغاة',
} as const

const paymentLabels = {
  unpaid: 'غير مدفوعة',
  partial: 'مدفوعة جزئيًا',
  paid: 'مدفوعة بالكامل',
} as const

function setRemainingPayment() {
  if (invoice.value) payAmount.value = invoice.value.amount_remaining
}

function setConfirmMode(mode: 'completed' | 'without_paid' | 'partial') {
  confirmMode.value = mode
}

function syncConfirmAmount(mode: 'completed' | 'without_paid' | 'partial') {
  if (!invoice.value) return
  if (mode === 'completed') {
    payAmount.value = invoice.value.total
    return
  }
  if (mode === 'without_paid') {
    payAmount.value = '0.00'
    return
  }
  if (!payAmount.value || payAmount.value === '0.00' || payAmount.value === invoice.value.total) {
    payAmount.value = invoice.value.amount_remaining
  }
}

async function handleAuthError(err: unknown) {
  if (err instanceof ApiError && err.status === 401) {
    auth.logout()
    await router.push({ name: 'login' })
  }
}

function apiErrorMessage(err: unknown, fallback: string) {
  if (err instanceof ApiError && err.body && typeof err.body === 'object') {
    const body = err.body as Record<string, unknown>
    const first = Object.values(body)[0]
    if (Array.isArray(first)) return String(first[0])
    if (typeof first === 'string') return first
  }
  return fallback
}

function needsQuantity(method?: CostMethod) {
  return method === 'quantity'
}

function needsOneDimension(method?: CostMethod) {
  return method === 'one_dimension' || (method as string) === 'area'
}

function needsTwoDimensions(method?: CostMethod) {
  return method === 'two_dimensions' || (method as string) === 'perimeter'
}

function needsDimensions(method?: CostMethod) {
  return needsOneDimension(method) || needsTwoDimensions(method)
}

function isFixedCost(service: Service) {
  return service.cost_method === 'fixed' || service.is_fixed_cost
}

function updateCalculatedPrices(source: 'unit' | 'total' | 'dims') {
  const service = selectedService.value
  if (!service) return

  const method = service.cost_method
  const length = pieceForm.length === '' ? null : Number(pieceForm.length)
  const width = pieceForm.width === '' ? null : Number(pieceForm.width)
  const quantity = itemForm.quantity === '' ? null : Number(itemForm.quantity)

  let measure = 1
  if (method === 'one_dimension' || (method as string) === 'area') {
    const dim = width ?? length ?? 0
    measure = dim * dim
  } else if (method === 'two_dimensions' || (method as string) === 'perimeter') {
    if (length != null && width != null) {
      measure = 2 * (length + width)
    }
  } else if (method === 'quantity') {
    measure = quantity ?? 1
  }

  if (source === 'total') {
    const total = Number(itemForm.total_price) || 0
    if (measure > 0) {
      itemForm.unit_price = roundMoney(total / measure).toString()
    }
  } else {
    const unitPrice = Number(itemForm.unit_price) || 0
    const calculatedTotal = computeLineSubtotal({
      costMethod: method,
      unitPrice,
      quantity,
      length,
      width,
    })
    itemForm.total_price = calculatedTotal.toString()
  }
}

function updateExtraCalculatedPrices(source: 'unit' | 'total' | 'dims') {
  const service = extraSelectedService.value
  if (!service) return

  const piece = extraPiece.value
  const method = service.cost_method
  const length =
    piece?.length != null
      ? Number(piece.length)
      : extraForm.length === ''
        ? null
        : Number(extraForm.length)
  const width =
    piece?.width != null
      ? Number(piece.width)
      : extraForm.width === ''
        ? null
        : Number(extraForm.width)
  const quantity = extraForm.quantity === '' ? null : Number(extraForm.quantity)

  let measure = 1
  if (method === 'one_dimension' || (method as string) === 'area') {
    const dim = width ?? length ?? 0
    measure = dim * dim
  } else if (method === 'two_dimensions' || (method as string) === 'perimeter') {
    if (length != null && width != null) {
      measure = 2 * (length + width)
    }
  } else if (method === 'quantity') {
    measure = quantity ?? 1
  }

  if (source === 'total') {
    const total = Number(extraForm.total_price) || 0
    if (measure > 0) {
      extraForm.unit_price = roundMoney(total / measure).toString()
    }
  } else {
    const unitPrice = Number(extraForm.unit_price) || 0
    const calculatedTotal = computeLineSubtotal({
      costMethod: method,
      unitPrice,
      quantity,
      length,
      width,
    })
    extraForm.total_price = calculatedTotal.toString()
  }
}

function resetServicePicker() {
  itemForm.service = ''
  itemForm.unit_price = ''
  itemForm.total_price = ''
  itemForm.quantity = ''
  itemForm.discount_amount = '0'
}

function resetPieceForm() {
  pieceForm.length = ''
  pieceForm.width = ''
  pieceForm.quantity = '1'
  draftServices.value = []
  resetServicePicker()
  itemError.value = null
}

function resetExtraForm() {
  extraForm.service = ''
  extraForm.unit_price = ''
  extraForm.total_price = ''
  extraForm.quantity = ''
  extraForm.discount_amount = '0'
  extraForm.length = ''
  extraForm.width = ''
  extraError.value = null
}

function onServiceChange() {
  const service = selectedService.value
  if (!service) return
  itemForm.unit_price = service.cost
  itemForm.category = service.service_category
  if (isFixedCost(service) || !needsQuantity(service.cost_method)) {
    itemForm.quantity = ''
  }
  updateCalculatedPrices('unit')
}

function onExtraServiceChange() {
  const service = extraSelectedService.value
  if (!service) return
  extraForm.unit_price = service.cost
  extraForm.category = service.service_category
  extraForm.length = ''
  extraForm.width = ''
  if (isFixedCost(service) || !needsQuantity(service.cost_method)) {
    extraForm.quantity = ''
  }
  updateExtraCalculatedPrices('unit')
}

watch(
  () => [extraForm.length, extraForm.width],
  () => updateExtraCalculatedPrices('dims'),
)

watch(
  () => itemForm.service,
  () => onServiceChange(),
)

watch(
  () => extraForm.service,
  () => onExtraServiceChange(),
)

watch(
  () => [pieceForm.length, pieceForm.width],
  () => {
    updateCalculatedPrices('dims')
  },
)

watch(confirmMode, (mode) => {
  syncConfirmAmount(mode)
})

watch(
  () => invoice.value?.total,
  () => {
    syncConfirmAmount(confirmMode.value)
  },
)

const showConfirmSuccess = ref(false)
const showConfirmDialog = ref(false)

const draftNeedsTwoDimensions = computed(() => {
  if (selectedService.value) {
    if (isFixedCost(selectedService.value) || selectedService.value.cost_method === 'fixed') return false
    return needsTwoDimensions(selectedService.value.cost_method)
  }
  return draftServices.value.some((row) => needsTwoDimensions(row.costMethod))
})

const draftNeedsOneDimension = computed(() => {
  if (selectedService.value) {
    if (isFixedCost(selectedService.value) || selectedService.value.cost_method === 'fixed') return false
    return needsOneDimension(selectedService.value.cost_method)
  }
  return draftServices.value.some((row) => needsOneDimension(row.costMethod))
})

const draftNeedsDimensions = computed(() => draftNeedsOneDimension.value || draftNeedsTwoDimensions.value)

const showDimensionInputs = computed(() => {
  if (selectedService.value) {
    if (isFixedCost(selectedService.value) || selectedService.value.cost_method === 'fixed' || selectedService.value.cost_method === 'quantity') {
      return false
    }
    return needsDimensions(selectedService.value.cost_method)
  }
  return draftNeedsDimensions.value
})

const showTwoDimensions = computed(() => {
  if (selectedService.value) {
    if (isFixedCost(selectedService.value) || selectedService.value.cost_method === 'fixed') return false
    return needsTwoDimensions(selectedService.value.cost_method)
  }
  return draftNeedsTwoDimensions.value
})

function serviceAmount(row: {
  costMethod: CostMethod
  unitPrice: string
  quantity: string
  discountAmount: string
}): number {
  const length = pieceForm.length === '' ? null : Number(pieceForm.length)
  const width = pieceForm.width === '' ? null : Number(pieceForm.width)
  const subtotal = computeLineSubtotal({
    costMethod: row.costMethod,
    unitPrice: Number(row.unitPrice) || 0,
    quantity: row.quantity === '' ? null : Number(row.quantity),
    length,
    width,
  })
  return applyDiscount(subtotal, Number(row.discountAmount) || 0)
}

const previewServices = computed(() => {
  const rows = [...draftServices.value]
  if (selectedService.value && itemForm.unit_price) {
    rows.push({
      key: 0,
      serviceId: selectedService.value.id,
      serviceName: selectedService.value.name,
      serviceColor: selectedService.value.color,
      costMethod: selectedService.value.cost_method,
      unitPrice: itemForm.unit_price,
      quantity: itemForm.quantity,
      discountAmount: itemForm.discount_amount,
    })
  }
  return rows
})

const piecePreview = computed(() => {
  const one = roundMoney(previewServices.value.reduce((sum, row) => sum + serviceAmount(row), 0))
  const qty = Number(pieceForm.quantity) || 1
  return { one, all: roundMoney(one * qty), qty }
})

function validateServiceRow(
  service: Service | undefined,
  unitPrice: string,
  quantity: string,
  requireDimensions: boolean,
): string | null {
  if (!service) return 'اختر خدمة.'
  if (!unitPrice) return 'السعر مطلوب.'
  if (needsQuantity(service.cost_method) && !quantity) return 'الكمية مطلوبة.'
  if (requireDimensions && !isFixedCost(service) && service.cost_method !== 'fixed') {
    if (needsTwoDimensions(service.cost_method) && (!pieceForm.length || !pieceForm.width)) {
      return 'الطول والعرض مطلوبان لهذه الخدمة.'
    }
    if (needsOneDimension(service.cost_method) && (!pieceForm.width && !pieceForm.length)) {
      return 'العرض (أو الطول) مطلوب لهذه الخدمة.'
    }
  }
  return null
}

function addServiceToDraft() {
  itemError.value = null
  const service = selectedService.value
  const error = validateServiceRow(service, itemForm.unit_price, itemForm.quantity, true)
  if (error || !service) {
    itemError.value = error
    return
  }
  draftServices.value.push({
    key: draftKey++,
    serviceId: service.id,
    serviceName: service.name,
    serviceColor: service.color,
    costMethod: service.cost_method,
    unitPrice: itemForm.unit_price,
    quantity: itemForm.quantity,
    discountAmount: itemForm.discount_amount || '0',
  })
  resetServicePicker()
}

async function addStandaloneItem() {
  if (savingItem.value || !invoice.value || !editable.value) return
  itemError.value = null

  const service = selectedService.value
  const error = validateServiceRow(service, itemForm.unit_price, itemForm.quantity, true)
  if (error || !service) {
    itemError.value = error
    return
  }

  savingItem.value = true
  try {
    await invoices.addItem(invoice.value.id, {
      service: service.id,
      unit_price: itemForm.unit_price,
      quantity: itemForm.quantity || undefined,
      discount_amount: itemForm.discount_amount || '0',
      length: pieceForm.length || undefined,
      width: pieceForm.width || undefined,
      piece_quantity: pieceForm.quantity,
    })
    resetPieceForm()
  } catch (err) {
    await handleAuthError(err)
    itemError.value = apiErrorMessage(err, 'تعذر إضافة الخدمة.')
  } finally {
    savingItem.value = false
  }
}

async function addPendingThroughItems(invoiceId: number, pending: DraftService[]) {
  let latest = invoices.current
  for (const [index, row] of pending.entries()) {
    const pieceId = index > 0 ? latest?.pieces?.[latest.pieces.length - 1]?.id : undefined
    latest = await invoices.addItem(invoiceId, {
      ...toItemPayload(row),
      length: pieceId == null ? pieceForm.length || undefined : undefined,
      width: pieceId == null ? pieceForm.width || undefined : undefined,
      piece: pieceId,
      piece_quantity: pieceId == null ? pieceForm.quantity : undefined,
    })
  }
}

function removeDraftService(key: number) {
  draftServices.value = draftServices.value.filter((row) => row.key !== key)
}

function toItemPayload(row: DraftService | {
  serviceId: number
  unitPrice: string
  quantity: string
  discountAmount: string
}): InvoicePieceItemPayload {
  return {
    service: row.serviceId,
    unit_price: row.unitPrice,
    quantity: row.quantity || undefined,
    discount_amount: row.discountAmount || '0',
  }
}

async function addPiece() {
  if (savingItem.value || !invoice.value || !editable.value) return
  itemError.value = null

  const pending: DraftService[] = [...draftServices.value]
  if (selectedService.value && itemForm.unit_price) {
    const error = validateServiceRow(
      selectedService.value,
      itemForm.unit_price,
      itemForm.quantity,
      true,
    )
    if (error) {
      itemError.value = error
      return
    }
    pending.push({
      key: 0,
      serviceId: selectedService.value.id,
      serviceName: selectedService.value.name,
      serviceColor: selectedService.value.color,
      costMethod: selectedService.value.cost_method,
      unitPrice: itemForm.unit_price,
      quantity: itemForm.quantity,
      discountAmount: itemForm.discount_amount || '0',
    })
  }

  if (!pending.length) {
    itemError.value = 'أضف خدمة واحدة على الأقل للقطعة.'
    return
  }
  const requiresTwo = pending.some((row) => needsTwoDimensions(row.costMethod))
  const requiresOne = pending.some((row) => needsOneDimension(row.costMethod))

  if (requiresTwo && (!pieceForm.length || !pieceForm.width)) {
    itemError.value = 'الطول والعرض مطلوبان.'
    return
  }
  if (requiresOne && (!pieceForm.width && !pieceForm.length)) {
    itemError.value = 'العرض مطلوب.'
    return
  }

  savingItem.value = true
  try {
    try {
      await invoices.addPiece(invoice.value.id, {
        length: pieceForm.length || undefined,
        width: pieceForm.width || undefined,
        quantity: '1',
        items: pending.map((row) => toItemPayload(row)),
      })
    } catch (err) {
      if (!(err instanceof ApiError) || err.status !== 404) throw err
      await addPendingThroughItems(invoice.value.id, pending)
    }
    resetPieceForm()
  } catch (err) {
    await handleAuthError(err)
    itemError.value = apiErrorMessage(err, 'تعذر إضافة القطعة.')
  } finally {
    savingItem.value = false
  }
}

async function addServiceToPiece(pieceId: number) {
  if (savingItem.value || !invoice.value || !editable.value) return
  extraError.value = null
  const service = extraSelectedService.value
  const piece = invoice.value.pieces.find((p) => p.id === pieceId)
  const pieceHasDims = piece?.length != null && piece?.width != null
  const error = validateServiceRow(service, extraForm.unit_price, extraForm.quantity, false)
  if (error || !service) {
    extraError.value = error
    return
  }
  if (needsDimensions(service.cost_method) && !pieceHasDims) {
    if (needsTwoDimensions(service.cost_method) && (!extraForm.length || !extraForm.width)) {
      extraError.value = 'الطول والعرض مطلوبان لهذه الخدمة.'
      return
    }
    if (needsOneDimension(service.cost_method) && !extraForm.width && !extraForm.length) {
      extraError.value = 'العرض (أو الطول) مطلوب لهذه الخدمة.'
      return
    }
  }

  savingItem.value = true
  try {
    await invoices.addItem(invoice.value.id, {
      service: service.id,
      unit_price: extraForm.unit_price,
      quantity: extraForm.quantity || undefined,
      discount_amount: extraForm.discount_amount || '0',
      piece: pieceId,
      length: pieceHasDims ? undefined : extraForm.length || undefined,
      width: pieceHasDims ? undefined : extraForm.width || undefined,
    })
    extraPieceId.value = null
    resetExtraForm()
  } catch (err) {
    await handleAuthError(err)
    extraError.value = apiErrorMessage(err, 'تعذر إضافة الخدمة.')
  } finally {
    savingItem.value = false
  }
}

function openExtraForm(pieceId: number) {
  extraPieceId.value = pieceId
  extraForm.category = availableCategories.value[0]?.id ?? ''
  resetExtraForm()
}

async function removeItem(itemId: number) {
  if (!invoice.value || !editable.value || acting.value) return
  acting.value = true
  try {
    await invoices.removeItem(invoice.value.id, itemId)
  } catch (err) {
    await handleAuthError(err)
    itemError.value = apiErrorMessage(err, 'تعذر حذف الخدمة.')
  } finally {
    acting.value = false
  }
}

async function removePiece(pieceId: number) {
  if (!invoice.value || !editable.value || acting.value) return
  acting.value = true
  try {
    await invoices.removePiece(invoice.value.id, pieceId)
  } catch (err) {
    await handleAuthError(err)
    itemError.value = apiErrorMessage(err, 'تعذر حذف القطعة.')
  } finally {
    acting.value = false
  }
}

async function loadLookups() {
  await Promise.all([clients.fetchAll(), categories.fetchAll(), services.fetchAll()])
  if (!header.client && clients.items[0]) header.client = clients.items[0].id
  if (!itemForm.category && availableCategories.value[0]) {
    itemForm.category = availableCategories.value[0].id
  }
  if (!extraForm.category && availableCategories.value[0]) {
    extraForm.category = availableCategories.value[0].id
  }
}

async function loadInvoice(id: number) {
  const data = await invoices.fetchOne(id)
  header.client = data.client
  header.discount_amount = data.discount_amount
  header.notes = data.notes
  header.issue_date = data.issue_date
  confirmMode.value = 'completed'
  syncConfirmAmount('completed')
}

async function saveAndContinue() {
  if (savingHeader.value) return
  headerError.value = null
  if (header.client === '' || header.client == null) {
    headerError.value = 'العميل مطلوب.'
    return
  }
  savingHeader.value = true
  try {
    if (isNew.value) {
      const created = await invoices.create({
        client: Number(header.client),
        discount_amount: header.discount_amount || '0',
        notes: header.notes,
        issue_date: header.issue_date,
      })
      await router.replace({ name: 'invoice-edit', params: { id: created.id } })
    } else if (invoice.value) {
      await invoices.updateHeader(invoice.value.id, {
        client: Number(header.client),
        discount_amount: header.discount_amount || '0',
        notes: header.notes,
        issue_date: header.issue_date,
      })
    }
  } catch (err) {
    await handleAuthError(err)
    headerError.value = apiErrorMessage(err, 'تعذر حفظ الفاتورة.')
  } finally {
    savingHeader.value = false
  }
}

async function confirm() {
  if (!invoice.value || acting.value) return
  if (!hasPieces.value) {
    itemError.value = 'أضف قطعة واحدة على الأقل قبل التأكيد.'
    return
  }
  let amount: string | undefined
  if (confirmMode.value === 'completed') {
    amount = invoice.value.total
  } else if (confirmMode.value === 'without_paid') {
    amount = undefined
  } else {
    amount = String(payAmount.value ?? '').trim()
    if (amount === '' || Number(amount) <= 0) {
      payError.value = 'أدخل مبلغ الدفع الجزئي.'
      return
    }
    if (Number(amount) > Number(invoice.value.total)) {
      payError.value = 'المبلغ المدفوع لا يمكن أن يتجاوز إجمالي الفاتورة.'
      return
    }
  }
  acting.value = true
  payError.value = null
  showConfirmSuccess.value = false
  showConfirmDialog.value = false
  try {
    await invoices.confirm(invoice.value.id, amount)
    payAmount.value = ''
    showConfirmSuccess.value = true
    showConfirmDialog.value = true
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (err) {
    await handleAuthError(err)
    payError.value = apiErrorMessage(err, 'تعذر تأكيد الفاتورة.')
  } finally {
    acting.value = false
  }
}

async function recordPayment() {
  if (!invoice.value || acting.value) return
  const amount = String(payAmount.value ?? '').trim()
  if (!amount || Number(amount) <= 0) {
    payError.value = 'أدخل مبلغ الدفع.'
    return
  }
  if (Number(amount) > Number(invoice.value.amount_remaining)) {
    payError.value = 'المبلغ أكبر من المتبقي على الفاتورة.'
    return
  }
  acting.value = true
  payError.value = null
  try {
    await invoices.pay(invoice.value.id, {
      amount,
      notes: String(payNotes.value ?? '').trim(),
    })
    payAmount.value = ''
    payNotes.value = ''
  } catch (err) {
    await handleAuthError(err)
    payError.value = apiErrorMessage(err, 'تعذر تسجيل الدفعة.')
  } finally {
    acting.value = false
  }
}

async function cancel() {
  if (!invoice.value || acting.value) return
  if (!window.confirm('هل تريد إلغاء الفاتورة؟')) return
  acting.value = true
  try {
    await invoices.cancel(invoice.value.id)
  } catch (err) {
    await handleAuthError(err)
    itemError.value = apiErrorMessage(err, 'تعذر إلغاء الفاتورة.')
  } finally {
    acting.value = false
  }
}

function pieceSizeLabel(length: string | null, width: string | null) {
  if (length != null && width != null && length !== '' && width !== '') return `${length} × ${width}`
  if (width != null && width !== '') return `${width}`
  if (length != null && length !== '') return `${length}`
  return 'بدون مقاس'
}

function itemDimensionLabel(
  item: { length?: string | null; width?: string | null; cost_method?: string },
  piece: { length: string | null; width: string | null },
): string | null {
  if (item.cost_method === 'fixed') return null
  const len = item.length ?? piece.length
  const wid = item.width ?? piece.width
  if (len != null && wid != null && len !== '' && wid !== '') return `${len} × ${wid}`
  if (wid != null && wid !== '') return `${wid}`
  if (len != null && len !== '') return `${len}`
  return null
}

function measureLabel(service: Service) {
  return costMethodLabels[service.cost_method] ?? service.cost_method
}

onMounted(async () => {
  try {
    await loadLookups()
    const routeId = props.id ?? (route.params.id as string | undefined)
    if (routeId) await loadInvoice(Number(routeId))
    else invoices.current = null
  } catch (err) {
    await handleAuthError(err)
  }
})

watch(
  () => props.id,
  async (id) => {
    if (id) {
      try {
        await loadInvoice(Number(id))
      } catch (err) {
        await handleAuthError(err)
      }
    }
  },
)
</script>

<template>
  <div class="page">
    <UiDialog v-model:open="showConfirmDialog" title="تم تأكيد الفاتورة بنجاح 🎉">
      <div class="confirm-dialog-content">
        <div class="success-icon-badge">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <p class="confirm-dialog-desc">
          تم تأكيد الفاتورة رقم <strong>{{ invoice?.number }}</strong> بنجاح.
        </p>
        <div class="confirm-dialog-details">
          <div class="detail-item">
            <span class="detail-label">إجمالي الفاتورة</span>
            <strong class="detail-value">{{ invoice?.total }} ج.م</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">المبلغ المدفوع</span>
            <strong class="detail-value text-success">{{ invoice?.amount_paid }} ج.م</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">المتبقي على العميل</span>
            <strong class="detail-value">{{ invoice?.amount_remaining }} ج.م</strong>
          </div>
        </div>
      </div>
      <template #footer>
        <UiButton class="full-width-btn" @click="showConfirmDialog = false">
          حسناً / إغلاق
        </UiButton>
      </template>
    </UiDialog>

    <div v-if="showConfirmSuccess" class="alert-success">
      <span>✓ تم تأكيد الفاتورة بنجاح!</span>
      <UiButton variant="ghost" size="sm" @click="showConfirmSuccess = false">إغلاق</UiButton>
    </div>

    <header class="page-header">
      <div>
        <h1>{{ isNew ? 'فاتورة جديدة' : invoice?.number }}</h1>
        <p v-if="invoice" class="muted">
          الحالة:
          <span class="pill" :data-status="invoice.status">
            {{ statusLabels[invoice.status] }}
          </span>
        </p>
        <p v-else class="muted">أدخل العميل ثم احفظ للمتابعة وإضافة القطع</p>
      </div>
      <UiButton variant="outline" @click="router.push({ name: 'invoices' })">
        رجوع
      </UiButton>
    </header>

    <UiCard>
      <h2 class="section-title">رأس الفاتورة</h2>
      <div class="grid">
        <div>
          <UiLabel>العميل</UiLabel>
          <UiSelect v-model="header.client" :disabled="!editable">
            <option disabled value="">اختر عميلًا</option>
            <option v-for="c in clients.items" :key="c.id" :value="c.id">
              {{ c.name }} — {{ c.phone }}
            </option>
          </UiSelect>
        </div>
        <div>
          <UiLabel>التاريخ</UiLabel>
          <UiInput v-model="header.issue_date" type="date" :disabled="!editable" />
        </div>
        <div>
          <UiLabel>خصم الفاتورة</UiLabel>
          <UiInput v-model="header.discount_amount" type="number" min="0" step="0.01" :disabled="!editable" />
        </div>
        <div class="full">
          <UiLabel>ملاحظات</UiLabel>
          <UiTextarea v-model="header.notes" :disabled="!editable" :rows="2" />
        </div>
      </div>
      <p v-if="headerError" class="error">{{ headerError }}</p>
      <div v-if="editable" class="actions">
        <UiButton :disabled="savingHeader" @click="saveAndContinue">
          {{ savingHeader ? 'جاري الحفظ...' : isNew ? 'حفظ ومتابعة' : 'حفظ الرأس' }}
        </UiButton>
      </div>
    </UiCard>

    <template v-if="invoice">
      <UiCard>
        <h2 class="section-title">قطع الفاتورة</h2>

        <div class="pieces">
          <article v-for="piece in invoicePieces" :key="piece.id" class="piece-card">
            <header class="piece-header">
              <div>
                <strong>قطعة {{ pieceSizeLabel(piece.length, piece.width) }}</strong>
                <p class="muted">عدد القطع: {{ piece.quantity }}</p>
              </div>
              <div class="piece-totals">
                <span>إجمالي القطعة {{ piece.piece_subtotal }}</span>
                <strong>إجمالي القطع {{ piece.piece_total }}</strong>
              </div>
            </header>

            <div class="piece-services">
              <div v-for="item in piece.items" :key="item.id" class="item-card">
                <div class="item-info">
                  <div
                    class="item-color-swatch"
                    :style="{ backgroundColor: item.service_color }"
                  ></div>
                  <div>
                    <strong>{{ item.service_name }}</strong>
                    <p class="muted">
                      {{ costMethodLabels[item.cost_method] ?? item.cost_method }}
                      <template v-if="itemDimensionLabel(item, piece)"> · المقاس: {{ itemDimensionLabel(item, piece) }}</template>
                      · سعر {{ item.unit_price }}
                      <template v-if="item.quantity"> · كمية {{ item.quantity }}</template>
                    </p>
                  </div>
                </div>
                <div class="item-total">
                  <span>{{ item.line_total }}</span>
                  <UiButton
                    v-if="editable"
                    variant="destructive"
                    size="sm"
                    :disabled="acting"
                    @click="removeItem(item.id)"
                  >
                    حذف
                  </UiButton>
                </div>
              </div>
            </div>

            <div v-if="editable" class="piece-actions">
              <UiButton
                variant="outline"
                size="sm"
                :disabled="acting"
                @click="openExtraForm(piece.id)"
              >
                إضافة خدمة لهذه القطعة
              </UiButton>
              <UiButton
                variant="destructive"
                size="sm"
                :disabled="acting"
                @click="removePiece(piece.id)"
              >
                حذف القطعة
              </UiButton>
            </div>

            <div v-if="editable && extraPieceId === piece.id" class="extra-form">
              <h4>خدمة إضافية</h4>
              <div class="grid">
                <div>
                  <UiLabel>تصنيف (فلتر)</UiLabel>
                  <UiSelect v-model="extraForm.category">
                    <option value="">الكل</option>
                    <option v-for="cat in availableCategories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </option>
                  </UiSelect>
                </div>
                <div>
                  <UiLabel>الخدمة</UiLabel>
                  <UiSelect v-model="extraForm.service">
                    <option disabled value="">اختر خدمة</option>
                    <option v-for="s in extraFilteredServices" :key="s.id" :value="s.id">
                      {{ s.name }} — {{ measureLabel(s) }}
                    </option>
                  </UiSelect>
                </div>
                <div v-if="extraSelectedService && needsQuantity(extraSelectedService.cost_method)">
                  <UiLabel>الكمية</UiLabel>
                  <UiInput
                    v-model="extraForm.quantity"
                    type="number"
                    min="0.001"
                    step="0.001"
                    @input="updateExtraCalculatedPrices('unit')"
                  />
                </div>
                <div v-if="showExtraDimensionInputs" class="grid">
                  <div v-if="showExtraTwoDimensions">
                    <UiLabel>الطول (x)</UiLabel>
                    <UiInput
                      v-model="extraForm.length"
                      type="number"
                      min="0"
                      step="0.001"
                      placeholder="أدخل الطول"
                    />
                  </div>
                  <div>
                    <UiLabel>{{ showExtraTwoDimensions ? 'العرض (y)' : 'البعد / العرض (x)' }}</UiLabel>
                    <UiInput
                      v-model="extraForm.width"
                      type="number"
                      min="0"
                      step="0.001"
                      placeholder="أدخل العرض / البعد"
                    />
                  </div>
                </div>
                <div v-if="extraSelectedService" class="grid full">
                  <div>
                    <UiLabel>السعر (الوحدة)</UiLabel>
                    <UiInput
                      v-model="extraForm.unit_price"
                      type="number"
                      min="0"
                      step="0.01"
                      @input="updateExtraCalculatedPrices('unit')"
                    />
                  </div>
                  <div>
                    <UiLabel>إجمالي سعر الخدمة للقطعة</UiLabel>
                    <UiInput
                      v-model="extraForm.total_price"
                      type="number"
                      min="0"
                      step="0.01"
                      @input="updateExtraCalculatedPrices('total')"
                    />
                  </div>
                  <div>
                    <UiLabel>خصم الخدمة</UiLabel>
                    <UiInput v-model="extraForm.discount_amount" type="number" min="0" step="0.01" />
                  </div>
                </div>
              </div>
              <p v-if="extraError" class="error">{{ extraError }}</p>
              <div class="actions">
                <UiButton :disabled="savingItem" @click="addServiceToPiece(piece.id)">
                  {{ savingItem ? 'جاري الإضافة...' : 'حفظ الخدمة' }}
                </UiButton>
                <UiButton
                  variant="outline"
                  @click="
                    () => {
                      extraPieceId = null
                      resetExtraForm()
                    }
                  "
                  >إلغاء</UiButton
                >
              </div>
            </div>
          </article>

          <div v-if="legacyInvoiceItems.length" class="piece-services legacy-items">
            <h3 class="legacy-title">الخدمات الحالية</h3>
            <div v-for="item in legacyInvoiceItems" :key="item.id" class="item-card">
              <div class="item-info">
                <div
                  class="item-color-swatch"
                  :style="{ backgroundColor: item.service_color }"
                ></div>
                <div>
                  <strong>{{ item.service_name }}</strong>
                  <p class="muted">
                    {{ costMethodLabels[item.cost_method] ?? item.cost_method }}
                    <template v-if="itemDimensionLabel(item, { length: null, width: null })"> · المقاس: {{ itemDimensionLabel(item, { length: null, width: null }) }}</template>
                    · سعر {{ item.unit_price }}
                    <template v-if="item.quantity"> · كمية {{ item.quantity }}</template>
                  </p>
                </div>
              </div>
              <div class="item-total">
                <span>{{ item.line_total }}</span>
                <UiButton
                  v-if="editable"
                  variant="destructive"
                  size="sm"
                  :disabled="acting"
                  @click="removeItem(item.id)"
                >
                  حذف الخدمة
                </UiButton>
              </div>
            </div>
          </div>

          <p v-if="!invoicePieces.length && !legacyInvoiceItems.length" class="muted">
            لا توجد خدمات بعد.
          </p>
        </div>

        <div v-if="editable" class="item-form">
          <h3>إضافة قطعة / خدمة</h3>
          <p class="hint">اختر الخدمة أولاً، ثم أدخل المقاسات أو الكمية والسعر.</p>

          <!-- 1. الخدمة والتصنيف أولاً -->
          <div class="grid">
            <div>
              <UiLabel>تصنيف (فلتر)</UiLabel>
              <UiSelect v-model="itemForm.category">
                <option value="">الكل</option>
                <option v-for="cat in availableCategories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </UiSelect>
            </div>
            <div>
              <UiLabel>الخدمة</UiLabel>
              <UiSelect v-model="itemForm.service">
                <option disabled value="">اختر خدمة</option>
                <option v-for="s in filteredServices" :key="s.id" :value="s.id">
                  {{ s.name }} — {{ measureLabel(s) }}
                </option>
              </UiSelect>
              <p v-if="selectedService" class="service-meta">
                <span class="pill" :data-fixed="isFixedCost(selectedService)">
                  {{ isFixedCost(selectedService) ? 'سعر ثابت' : 'سعر غير ثابت' }}
                </span>
              </p>
            </div>
          </div>

          <!-- 2. المقاسات بناءً على الخدمة المحددة (أو باقي الخدمات المضافة للقطعة) -->
          <div
            v-if="draftNeedsDimensions || (selectedService && needsDimensions(selectedService.cost_method))"
            class="grid"
          >
            <div v-if="draftNeedsTwoDimensions || (selectedService && needsTwoDimensions(selectedService.cost_method))">
              <UiLabel>الطول (x)</UiLabel>
              <UiInput
                v-model="pieceForm.length"
                type="number"
                min="0"
                step="0.001"
                placeholder="أدخل الطول"
                @input="updateCalculatedPrices('dims')"
              />
            </div>
            <div v-if="draftNeedsDimensions || (selectedService && needsDimensions(selectedService.cost_method))">
              <UiLabel>{{ (selectedService && needsOneDimension(selectedService.cost_method)) || (draftNeedsOneDimension && !draftNeedsTwoDimensions) ? 'البعد / العرض (x)' : 'العرض (y)' }}</UiLabel>
              <UiInput
                v-model="pieceForm.width"
                type="number"
                min="0"
                step="0.001"
                placeholder="أدخل العرض / البعد"
                @input="updateCalculatedPrices('dims')"
              />
            </div>
          </div>

          <!-- 3. الكمية للخدمة (إن كانت ذات كمية) -->
          <div v-if="selectedService && needsQuantity(selectedService.cost_method)" class="grid">
            <div>
              <UiLabel>الكمية</UiLabel>
              <UiInput
                v-model="itemForm.quantity"
                type="number"
                min="0.001"
                step="0.001"
                @input="updateCalculatedPrices('unit')"
              />
            </div>
          </div>

          <!-- 4. سعر الوحدة وإجمالي سعر الخدمة للقطعة وخصم الخدمة -->
          <div v-if="selectedService" class="grid">
            <div>
              <UiLabel>سعر الوحدة</UiLabel>
              <UiInput
                v-model="itemForm.unit_price"
                type="number"
                min="0"
                step="0.01"
                @input="updateCalculatedPrices('unit')"
              />
            </div>
            <div>
              <UiLabel>إجمالي سعر الخدمة للقطعة</UiLabel>
              <UiInput
                v-model="itemForm.total_price"
                type="number"
                min="0"
                step="0.01"
                @input="updateCalculatedPrices('total')"
              />
            </div>
            <div>
              <UiLabel>خصم الخدمة</UiLabel>
              <UiInput
                v-model="itemForm.discount_amount"
                type="number"
                min="0"
                step="0.01"
                @input="updateCalculatedPrices('unit')"
              />
            </div>
          </div>

          <!-- 5. الخدمات المؤقتة المضافة لهذه القطعة -->
          <div v-if="draftServices.length" class="draft-list">
            <h4>الخدمات المضافة لهذه القطعة:</h4>
            <div v-for="row in draftServices" :key="row.key" class="draft-row">
              <span
                class="item-color-swatch"
                :style="{ backgroundColor: row.serviceColor }"
              ></span>
              <span>{{ row.serviceName }} · {{ costMethodLabels[row.costMethod] }}</span>
              <strong>{{ serviceAmount(row).toFixed(2) }} ج.م</strong>
              <UiButton variant="destructive" size="sm" @click="removeDraftService(row.key)">حذف</UiButton>
            </div>
          </div>

          <!-- 6. معاينة الإجمالي والزر -->
          <div v-if="previewServices.length" class="preview">
            <div class="summary-row total">
              <span>إجمالي القطعة</span>
              <strong>{{ piecePreview.one.toFixed(2) }}</strong>
            </div>
          </div>

          <p v-if="itemError" class="error">{{ itemError }}</p>
          <div class="actions">
            <UiButton variant="outline" :disabled="savingItem" @click="addServiceToDraft">
              إضافة خدمة أخرى للقطعة
            </UiButton>
            <UiButton :disabled="savingItem" @click="addPiece">
              {{ savingItem ? 'جاري الإضافة...' : 'حفظ القطعة' }}
            </UiButton>
          </div>
        </div>
      </UiCard>

      <UiCard class="summary sticky">
        <h2 class="section-title">الملخص</h2>
        <div class="summary-row"><span>مجموع القطع</span><strong>{{ invoice.subtotal }}</strong></div>
        <div class="summary-row"><span>خصم الفاتورة</span><strong>{{ invoice.discount_amount }}</strong></div>
        <div class="summary-row total"><span>الإجمالي</span><strong>{{ invoice.total }}</strong></div>
        <template v-if="invoice.status !== 'draft'">
          <div class="summary-row"><span>المدفوع</span><strong>{{ invoice.amount_paid }}</strong></div>
          <div class="summary-row">
            <span>المتبقي (عهدة العميل)</span>
            <strong>{{ invoice.amount_remaining }}</strong>
          </div>
          <div class="summary-row">
            <span>حالة الدفع</span>
            <strong>{{ paymentLabels[invoice.payment_status] }}</strong>
          </div>
        </template>

        <div v-if="invoice.status === 'draft'" class="pay-box">
          <UiLabel>طريقة التأكيد</UiLabel>
          <UiSelect v-model="confirmMode">
            <option value="completed">مكتملة</option>
            <option value="without_paid">بدون دفع</option>
            <option value="partial">جزئي</option>
          </UiSelect>

          <UiLabel html-for="confirm-pay">المبلغ المدفوع عند التأكيد</UiLabel>
          <UiInput
            id="confirm-pay"
            v-model="payAmount"
            type="number"
            min="0"
            step="0.01"
            :disabled="confirmMode !== 'partial'"
            :placeholder="
              confirmMode === 'completed'
                ? 'مكتملة'
                : confirmMode === 'without_paid'
                  ? 'بدون دفع'
                  : 'أدخل المبلغ الجزئي'
            "
          />
          <div class="pay-actions">
            <UiButton type="button" variant="outline" size="sm" @click="setConfirmMode('completed')">
              مكتملة
            </UiButton>
            <UiButton type="button" variant="outline" size="sm" @click="setConfirmMode('without_paid')">
              بدون دفع
            </UiButton>
            <UiButton type="button" variant="outline" size="sm" @click="setConfirmMode('partial')">
              جزئي
            </UiButton>
          </div>
          <p class="hint">
            {{ confirmMode === 'partial' ? 'المتبقي بعد الدفع يُسجَّل عهدة على العميل.' : 'يمكن تغيير المبلغ فقط عند اختيار جزئي.' }}
          </p>
        </div>

        <div
          v-else-if="invoice.status === 'confirmed' && Number(invoice.amount_remaining) > 0"
          class="pay-box"
        >
          <UiLabel html-for="extra-pay">تسجيل دفعة / وديعة</UiLabel>
          <UiInput
            id="extra-pay"
            v-model="payAmount"
            type="number"
            min="0"
            step="0.01"
            :placeholder="`المتبقي ${invoice.amount_remaining}`"
          />
          <UiInput v-model="payNotes" placeholder="ملاحظات الدفع (اختياري)" />
          <div class="pay-actions">
            <UiButton type="button" variant="outline" size="sm" @click="setRemainingPayment">
              المتبقي كاملًا
            </UiButton>
            <UiButton type="button" :disabled="acting" @click="recordPayment">
              {{ acting ? 'جارٍ التسجيل…' : 'تسجيل الدفعة' }}
            </UiButton>
          </div>
        </div>

        <p v-if="payError" class="error">{{ payError }}</p>

        <div class="actions">
          <UiButton
            v-if="invoice.status === 'draft'"
            :disabled="acting || !hasPieces"
            @click="confirm"
          >
            تأكيد الفاتورة
          </UiButton>
          <UiButton
            v-if="invoice.status !== 'cancelled'"
            variant="destructive"
            :disabled="acting"
            @click="cancel"
          >
            إلغاء الفاتورة
          </UiButton>
        </div>
      </UiCard>
    </template>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
  padding-bottom: 5rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.page-header h1 {
  margin: 0;
  font-size: 1.5rem;
}
.section-title {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}
.muted {
  color: hsl(var(--muted-foreground));
  margin: 0.35rem 0 0;
}
.error {
  color: hsl(var(--destructive));
}
.grid {
  display: grid;
  gap: 0.85rem;
}
@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .full {
    grid-column: 1 / -1;
  }
}
.field-pair {
  display: grid;
  gap: 0.85rem;
}
@media (min-width: 768px) {
  .field-pair {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .field-pair.full {
    grid-column: 1 / -1;
  }
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}
.pieces {
  display: grid;
  gap: 1rem;
  margin-bottom: 1.25rem;
}
.piece-card {
  display: grid;
  gap: 0.75rem;
  padding: 0.85rem 0;
  border-bottom: 1px solid hsl(var(--border));
}
.piece-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.piece-totals {
  display: grid;
  gap: 0.2rem;
  justify-items: end;
  font-size: 0.95rem;
}
.piece-services {
  display: grid;
  gap: 0.35rem;
}
.item-card {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.5rem 0;
}
.item-info {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}
.item-color-swatch {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 0.375rem;
  border: 1px solid hsl(var(--border));
  flex-shrink: 0;
  margin-top: 0.1rem;
}
.item-total {
  display: grid;
  gap: 0.5rem;
  justify-items: end;
  font-weight: 600;
}
.piece-actions,
.draft-list {
  display: grid;
  gap: 0.5rem;
}
.draft-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.extra-form,
.item-form {
  display: grid;
  gap: 0.85rem;
  padding-top: 0.5rem;
  border-top: 1px solid hsl(var(--border));
}
.item-form h3,
.extra-form h4 {
  margin: 0;
  font-size: 1rem;
}
.service-meta {
  margin: 0.4rem 0 0;
}
.preview {
  padding-top: 0.5rem;
}
.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0;
}
.summary-row.total {
  font-size: 1.15rem;
  border-top: 1px solid hsl(var(--border));
  margin-top: 0.35rem;
  padding-top: 0.75rem;
}
.pay-box {
  display: grid;
  gap: 0.55rem;
  margin-top: 0.85rem;
  padding-top: 0.85rem;
  border-top: 1px solid hsl(var(--border));
}
.pay-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.hint {
  margin: 0;
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
}
.pill {
  display: inline-flex;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  background: hsl(var(--muted));
}
.pill[data-fixed='true'] {
  background: hsl(142 40% 90%);
  color: hsl(142 50% 25%);
}
.pill[data-status='confirmed'] {
  background: hsl(142 40% 90%);
  color: hsl(142 50% 25%);
}
.pill[data-status='cancelled'] {
  background: hsl(0 40% 92%);
  color: hsl(0 45% 35%);
}
@media (max-width: 767px) {
  .sticky {
    position: sticky;
    bottom: 0.5rem;
    z-index: 5;
  }
}
.confirm-dialog-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0.75rem 0;
  gap: 0.85rem;
}
.success-icon-badge {
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  background: hsl(142 50% 92%);
  color: hsl(142 65% 35%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px hsl(142 50% 50% / 0.2);
}
.confirm-dialog-desc {
  margin: 0;
  font-size: 1rem;
  color: hsl(var(--foreground));
}
.confirm-dialog-details {
  width: 100%;
  background: hsl(var(--muted) / 0.5);
  border-radius: calc(var(--radius) - 2px);
  padding: 0.85rem 1rem;
  display: grid;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}
.detail-label {
  color: hsl(var(--muted-foreground));
}
.text-success {
  color: hsl(142 65% 35%);
}
.full-width-btn {
  width: 100%;
}
</style>
