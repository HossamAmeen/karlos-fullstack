<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import {
  createClientDeposit,
  getClientStatement,
  type ClientStatement,
  type PaymentStatus,
} from '@/api/clients'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ id: string }>()

const auth = useAuthStore()
const router = useRouter()

const statement = ref<ClientStatement | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const depositForm = reactive({
  amount: '',
  notes: '',
})

const paymentLabels: Record<PaymentStatus, string> = {
  unpaid: 'غير مدفوعة',
  partial: 'جزئي',
  paid: 'كامل',
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

async function load() {
  loading.value = true
  error.value = null
  try {
    statement.value = await getClientStatement(Number(props.id))
  } catch (err) {
    await handleAuthError(err)
    error.value = err instanceof ApiError ? 'تعذر تحميل كشف الحساب.' : 'فشل التحميل.'
  } finally {
    loading.value = false
  }
}

async function addDeposit() {
  formError.value = null
  if (!depositForm.amount || Number(depositForm.amount) <= 0) {
    formError.value = 'أدخل مبلغ الوديعة.'
    return
  }
  saving.value = true
  try {
    statement.value = await createClientDeposit(Number(props.id), {
      amount: depositForm.amount,
      notes: depositForm.notes.trim(),
    })
    depositForm.amount = ''
    depositForm.notes = ''
  } catch (err) {
    await handleAuthError(err)
    formError.value = apiErrorMessage(err, 'تعذر تسجيل الوديعة.')
  } finally {
    saving.value = false
  }
}

function openInvoice(invoiceId: number) {
  void router.push({ name: 'invoice-edit', params: { id: invoiceId } })
}

onMounted(() => {
  void load()
})

watch(
  () => props.id,
  () => {
    void load()
  },
)
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>كشف حساب العميل</h1>
        <p v-if="statement" class="muted">
          {{ statement.client.name }} — {{ statement.client.phone }}
        </p>
      </div>
      <UiButton variant="outline" @click="router.push({ name: 'clients' })">رجوع</UiButton>
    </header>

    <p v-if="loading" class="muted">جارٍ التحميل…</p>
    <p v-else-if="error" class="ui-error">{{ error }}</p>

    <template v-else-if="statement">
      <div class="stats">
        <UiCard>
          <p class="stat-label">إجمالي الفواتير (عليه)</p>
          <p class="stat-value">{{ statement.total_charged }}</p>
        </UiCard>
        <UiCard>
          <p class="stat-label">إجمالي المقبوضات / الودائع (له)</p>
          <p class="stat-value">{{ statement.total_deposits }}</p>
        </UiCard>
        <UiCard>
          <p class="stat-label">الرصيد المتبقي</p>
          <p class="stat-value" :data-due="Number(statement.balance_due) > 0">
            {{ statement.balance_due }}
          </p>
        </UiCard>
      </div>

      <UiCard>
        <h2 class="section-title">الفواتير المستحقة على العميل</h2>
        <div class="ui-table-wrap">
          <table class="ui-table">
            <thead>
              <tr>
                <th>الفاتورة</th>
                <th>التاريخ</th>
                <th>الحالة</th>
                <th>المبلغ (عليه)</th>
                <th>المدفوع / وديعة</th>
                <th>المتبقي</th>
                <th>الدفع</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="statement.invoices.length === 0">
                <td colspan="7" class="ui-empty">لا توجد فواتير مؤكدة أو ملغاة بعد.</td>
              </tr>
              <tr
                v-for="inv in statement.invoices"
                :key="inv.id"
                class="row-link"
                @click="openInvoice(inv.id)"
              >
                <td>{{ inv.number }}</td>
                <td>{{ inv.issue_date }}</td>
                <td>{{ inv.status === 'confirmed' ? 'مؤكدة' : 'ملغاة' }}</td>
                <td>{{ inv.total }}</td>
                <td>{{ inv.amount_paid }}</td>
                <td>{{ inv.amount_remaining }}</td>
                <td>{{ paymentLabels[inv.payment_status] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </UiCard>

      <UiCard>
        <h2 class="section-title">المقبوضات والودائع</h2>
        <form class="deposit-form" @submit.prevent="addDeposit">
          <div class="ui-field">
            <UiLabel html-for="deposit-amount">تسجيل وديعة / إيصال قبض</UiLabel>
            <UiInput
              id="deposit-amount"
              v-model="depositForm.amount"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </div>
          <div class="ui-field">
            <UiLabel html-for="deposit-notes">ملاحظات</UiLabel>
            <UiInput id="deposit-notes" v-model="depositForm.notes" />
          </div>
          <UiButton type="submit" :disabled="saving">
            {{ saving ? 'جارٍ الحفظ…' : 'إضافة وديعة' }}
          </UiButton>
        </form>
        <p v-if="formError" class="ui-error">{{ formError }}</p>

        <div class="ui-table-wrap">
          <table class="ui-table">
            <thead>
              <tr>
                <th>التاريخ</th>
                <th>المبلغ (وديعة)</th>
                <th>الفاتورة</th>
                <th>ملاحظات</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="statement.deposits.length === 0">
                <td colspan="4" class="ui-empty">لا توجد مقبوضات بعد.</td>
              </tr>
              <tr v-for="dep in statement.deposits" :key="dep.id">
                <td>{{ dep.paid_at }}</td>
                <td>{{ dep.amount }}</td>
                <td>{{ dep.invoice_number || 'وديعة عامة' }}</td>
                <td>{{ dep.notes || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </UiCard>
    </template>
  </section>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
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
.muted {
  color: hsl(var(--muted-foreground));
  margin: 0.35rem 0 0;
}
.stats {
  display: grid;
  gap: 0.75rem;
}
@media (min-width: 768px) {
  .stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
.stat-label {
  margin: 0;
  color: hsl(var(--muted-foreground));
  font-size: 0.9rem;
}
.stat-value {
  margin: 0.35rem 0 0;
  font-size: 1.4rem;
  font-weight: 700;
}
.stat-value[data-due='true'] {
  color: hsl(var(--destructive));
}
.section-title {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}
.deposit-form {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (min-width: 768px) {
  .deposit-form {
    grid-template-columns: 1fr 1fr auto;
    align-items: end;
  }
}
.row-link {
  cursor: pointer;
}
.row-link:hover {
  background: hsl(var(--muted) / 0.35);
}
</style>
