<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { ApiError } from '@/api/client'
import { createClientDeposit, getClientStatement, type Client } from '@/api/clients'
import { listInvoices, type Invoice } from '@/api/invoices'
import ClientPicker from '@/components/ClientPicker.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { paymentMethodOptions, type PaymentMethod } from '@/utils/paymentMethods'

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()

const clientId = ref<number | string>('')
const invoiceId = ref<number | string>('')
const amount = ref('')
const method = ref<PaymentMethod>('cash')
const notes = ref('')
const error = ref<string | null>(null)
const saving = ref(false)
const clientName = ref('')
const clientDebt = ref<number | null>(null)
const openInvoices = ref<Invoice[]>([])
const loadingInvoices = ref(false)

const selectedInvoice = computed(() =>
  openInvoices.value.find((i) => String(i.id) === String(invoiceId.value)) ?? null,
)

function reset() {
  clientId.value = ''
  invoiceId.value = ''
  amount.value = ''
  method.value = 'cash'
  notes.value = ''
  error.value = null
  openInvoices.value = []
  clientName.value = ''
  clientDebt.value = null
}

watch(open, (value) => {
  if (value) reset()
})

function onClientSelected(client: Client) {
  clientName.value = client.name
}

async function loadDebt(id: number | string) {
  clientDebt.value = null
  try {
    const statement = await getClientStatement(Number(id))
    if (String(clientId.value) === String(id)) clientDebt.value = Number(statement.balance_due)
  } catch {
    clientDebt.value = null
  }
}

watch(clientId, async (id) => {
  invoiceId.value = ''
  openInvoices.value = []
  clientDebt.value = null
  if (id === '' || id == null) return
  void loadDebt(id)
  loadingInvoices.value = true
  try {
    const data = await listInvoices({ client: Number(id), status: 'confirmed', limit: 100 })
    if (String(clientId.value) === String(id)) {
      openInvoices.value = data.results.filter((i) => Number(i.amount_remaining) > 0)
    }
  } catch {
    openInvoices.value = []
  } finally {
    loadingInvoices.value = false
  }
})

function fillRemaining() {
  if (selectedInvoice.value) amount.value = selectedInvoice.value.amount_remaining
}

function errorMessage(err: unknown) {
  if (err instanceof ApiError && err.body && typeof err.body === 'object') {
    const first = Object.values(err.body as Record<string, unknown>)[0]
    if (Array.isArray(first)) return String(first[0])
    if (typeof first === 'string') return first
  }
  return 'تعذر تسجيل الوديعة.'
}

async function submit() {
  error.value = null
  if (clientId.value === '') {
    error.value = 'اختر العميل.'
    return
  }
  const value = Number(amount.value)
  if (!amount.value || !(value > 0)) {
    error.value = 'أدخل مبلغ الوديعة.'
    return
  }
  if (selectedInvoice.value && value > Number(selectedInvoice.value.amount_remaining)) {
    error.value = `المبلغ أكبر من المتبقي على الفاتورة (${selectedInvoice.value.amount_remaining}).`
    return
  }
  saving.value = true
  try {
    await createClientDeposit(Number(clientId.value), {
      amount: amount.value,
      method: method.value,
      notes: notes.value.trim(),
      ...(selectedInvoice.value ? { invoice: selectedInvoice.value.id } : {}),
    })
    open.value = false
    emit('saved')
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UiDialog v-model:open="open" title="إضافة وديعة" description="سجّل مبلغًا مستلمًا من العميل، ويمكن ربطه بفاتورة محددة.">
    <form @submit.prevent="submit">
      <div class="ui-field">
        <UiLabel>العميل</UiLabel>
        <ClientPicker v-model="clientId" @select="onClientSelected" />
      </div>
      <div v-if="clientId !== '' && clientName" class="client-box">
        <div>العميل: <strong>{{ clientName }}</strong></div>
        <div v-if="clientDebt != null" class="debt" :class="{ owes: clientDebt > 0 }">
          مجموع المطلوب من العميل: <strong>{{ clientDebt > 0 ? clientDebt.toFixed(2) : '0.00' }}</strong>
          <span v-if="clientDebt <= 0"> (لا توجد مديونية)</span>
          <span v-if="clientDebt < 0"> — رصيد للعميل {{ Math.abs(clientDebt).toFixed(2) }}</span>
        </div>
        <div v-else class="debt">جاري تحميل المديونية...</div>
      </div>
      <div class="ui-field">
        <UiLabel html-for="dep-invoice">الفاتورة (اختياري)</UiLabel>
        <UiSelect id="dep-invoice" v-model="invoiceId" :disabled="clientId === '' || loadingInvoices">
          <option value="">وديعة عامة (بدون فاتورة)</option>
          <option v-for="inv in openInvoices" :key="inv.id" :value="inv.id">
            {{ inv.number }} — المتبقي {{ inv.amount_remaining }}
          </option>
        </UiSelect>
      </div>
      <div class="ui-field">
        <UiLabel html-for="dep-amount">المبلغ</UiLabel>
        <UiInput
          id="dep-amount"
          v-model="amount"
          type="number"
          min="0.01"
          :step="0.01"
          :placeholder="selectedInvoice ? `الحد الأقصى ${selectedInvoice.amount_remaining}` : ''"
          required
        />
        <UiButton v-if="selectedInvoice" type="button" variant="outline" size="sm" @click="fillRemaining">
          المتبقي كاملًا
        </UiButton>
      </div>
      <div class="ui-field">
        <UiLabel html-for="dep-method">طريقة الدفع</UiLabel>
        <UiSelect id="dep-method" v-model="method">
          <option v-for="m in paymentMethodOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </UiSelect>
      </div>
      <div class="ui-field">
        <UiLabel html-for="dep-notes">ملاحظات</UiLabel>
        <UiInput id="dep-notes" v-model="notes" />
      </div>

      <p v-if="error" class="ui-error">{{ error }}</p>

      <div class="ui-dialog-footer">
        <UiButton type="submit" :disabled="saving">{{ saving ? 'جارٍ الحفظ…' : 'حفظ' }}</UiButton>
        <UiButton type="button" variant="outline" @click="open = false">إلغاء</UiButton>
      </div>
    </form>
  </UiDialog>
</template>

<style scoped>
.client-box {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border: 1px solid hsl(var(--border));
  border-radius: 0.75rem;
  background: hsl(var(--muted) / 0.35);
  font-size: 1.1rem;
}
.client-box .debt {
  margin-top: 0.25rem;
  font-size: 1rem;
  color: hsl(142 50% 28%);
}
.client-box .debt.owes {
  color: hsl(0 60% 40%);
}
</style>
