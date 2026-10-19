<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import {
  createClientDeposit,
  getClientStatement,
  type ClientStatement,
  type PaymentStatus,
} from '@/api/clients'
import { createExpense, listExpenses, type Expense } from '@/api/expenses'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import { useAuthStore } from '@/stores/auth'
import { useExpenseCategoriesStore } from '@/stores/expenseCategories'

const props = defineProps<{ id: string }>()

const auth = useAuthStore()
const router = useRouter()

const lookups = useExpenseCategoriesStore()

const expenseItems = ref<Expense[]>([])
const expensesCount = ref(0)
const expensesPage = ref(1)
const expensesLoading = ref(false)
const expenseDialogOpen = ref(false)
const expenseSaving = ref(false)
const expenseError = ref<string | null>(null)
const expenseForm = reactive({
  amount: '',
  expense_date: new Date().toISOString().split('T')[0],
  category: null as number | null,
  description: '',
})
const expensesTotalPages = computed(() => Math.max(1, Math.ceil(expensesCount.value / 20)))

async function loadExpenses() {
  expensesLoading.value = true
  try {
    const data = await listExpenses({
      client: Number(props.id),
      limit: 20,
      offset: (expensesPage.value - 1) * 20,
    })
    expenseItems.value = data.results
    expensesCount.value = data.count
    const last = Math.max(1, Math.ceil(data.count / 20))
    if (expensesPage.value > last) {
      expensesPage.value = last
      await loadExpenses()
    }
  } catch (err) {
    await handleAuthError(err)
  } finally {
    expensesLoading.value = false
  }
}

function goToExpensesPage(page: number) {
  expensesPage.value = page
  void loadExpenses()
}

function openExpenseDialog() {
  expenseForm.amount = ''
  expenseForm.expense_date = new Date().toISOString().split('T')[0]
  expenseForm.category = null
  expenseForm.description = ''
  expenseError.value = null
  expenseDialogOpen.value = true
}

async function addExpense() {
  expenseError.value = null
  if (!expenseForm.amount || Number(expenseForm.amount) <= 0) {
    expenseError.value = 'المبلغ يجب أن يكون أكبر من صفر.'
    return
  }
  if (!expenseForm.category) {
    expenseError.value = 'التصنيف الفرعي مطلوب.'
    return
  }
  if (!expenseForm.description.trim()) {
    expenseError.value = 'الوصف مطلوب.'
    return
  }
  expenseSaving.value = true
  try {
    await createExpense({
      amount: expenseForm.amount,
      description: expenseForm.description.trim(),
      expense_date: expenseForm.expense_date,
      category: expenseForm.category,
      client: Number(props.id),
    })
    expenseDialogOpen.value = false
    expensesPage.value = 1
    await loadExpenses()
  } catch (err) {
    await handleAuthError(err)
    expenseError.value = apiErrorMessage(err, 'تعذر حفظ المصروف.')
  } finally {
    expenseSaving.value = false
  }
}

const statement = ref<ClientStatement | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

type StatementTab = 'invoices' | 'deposits' | 'expenses'
const activeTab = ref<StatementTab>('invoices')
const tabs: { key: StatementTab; label: string }[] = [
  { key: 'invoices', label: 'إظهار الفواتير' },
  { key: 'deposits', label: 'إظهار المدفوعات' },
  { key: 'expenses', label: 'إظهار المصروفات' },
]

const PAGE_SIZE = 20
const invoicesPage = ref(1)
const depositsPage = ref(1)

function pageCount(total: number) {
  return Math.max(1, Math.ceil(total / PAGE_SIZE))
}
function paginate<T>(rows: T[], page: number) {
  return rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
}

const invoicesTotalPages = computed(() => pageCount(statement.value?.invoices.length ?? 0))
const depositsTotalPages = computed(() => pageCount(statement.value?.deposits.length ?? 0))
const pagedInvoices = computed(() => paginate(statement.value?.invoices ?? [], invoicesPage.value))
const pagedDeposits = computed(() => paginate(statement.value?.deposits ?? [], depositsPage.value))

// Keep the current page valid after the statement reloads or a deposit is added.
watch(statement, () => {
  invoicesPage.value = Math.min(invoicesPage.value, invoicesTotalPages.value)
  depositsPage.value = Math.min(depositsPage.value, depositsTotalPages.value)
})

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
  void loadExpenses()
  lookups.fetchCategories(null, 'main_category__name,order_number,name').catch(handleAuthError)
})

watch(
  () => props.id,
  () => {
    invoicesPage.value = 1
    depositsPage.value = 1
    expensesPage.value = 1
    void load()
    void loadExpenses()
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
        <UiCard>
          <p class="stat-label">إجمالي المصروفات</p>
          <p class="stat-value">{{ statement.total_expenses }}</p>
        </UiCard>
      </div>

      <div class="tabs" role="tablist">
        <UiButton
          v-for="tab in tabs"
          :key="tab.key"
          role="tab"
          :aria-selected="activeTab === tab.key"
          :variant="activeTab === tab.key ? 'default' : 'outline'"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </UiButton>
      </div>

      <UiCard v-show="activeTab === 'invoices'">
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
                v-for="inv in pagedInvoices"
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
        <div v-if="invoicesTotalPages > 1" class="pagination">
          <UiButton variant="outline" size="sm" :disabled="invoicesPage <= 1" @click="invoicesPage--">
            السابق
          </UiButton>
          <span>صفحة {{ invoicesPage }} من {{ invoicesTotalPages }}</span>
          <UiButton variant="outline" size="sm" :disabled="invoicesPage >= invoicesTotalPages" @click="invoicesPage++">
            التالي
          </UiButton>
        </div>
      </UiCard>

      <UiCard v-show="activeTab === 'deposits'">
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
              <tr v-for="dep in pagedDeposits" :key="dep.id">
                <td>{{ dep.paid_at }}</td>
                <td>{{ dep.amount }}</td>
                <td>{{ dep.invoice_number || 'وديعة عامة' }}</td>
                <td>{{ dep.notes || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="depositsTotalPages > 1" class="pagination">
          <UiButton variant="outline" size="sm" :disabled="depositsPage <= 1" @click="depositsPage--">
            السابق
          </UiButton>
          <span>صفحة {{ depositsPage }} من {{ depositsTotalPages }}</span>
          <UiButton variant="outline" size="sm" :disabled="depositsPage >= depositsTotalPages" @click="depositsPage++">
            التالي
          </UiButton>
        </div>
      </UiCard>

      <UiCard v-show="activeTab === 'expenses'">
        <div class="section-head">
          <h2 class="section-title">مصروفات العميل</h2>
          <UiButton size="sm" @click="openExpenseDialog">إضافة مصروف</UiButton>
        </div>
        <div class="ui-table-wrap">
          <table class="ui-table">
            <thead>
              <tr>
                <th>التاريخ</th>
                <th>التصنيف</th>
                <th>الوصف</th>
                <th>المبلغ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="expensesLoading">
                <td colspan="4" class="ui-empty">جارٍ التحميل…</td>
              </tr>
              <tr v-else-if="expenseItems.length === 0">
                <td colspan="4" class="ui-empty">لا توجد مصروفات لهذا العميل.</td>
              </tr>
              <tr v-for="exp in expenseItems" :key="exp.id">
                <td>{{ exp.expense_date }}</td>
                <td>{{ exp.main_category_name }} / {{ exp.category_name }}</td>
                <td>{{ exp.description }}</td>
                <td>{{ exp.amount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="expensesTotalPages > 1" class="pagination">
          <UiButton variant="outline" size="sm" :disabled="expensesPage <= 1" @click="goToExpensesPage(expensesPage - 1)">
            السابق
          </UiButton>
          <span>صفحة {{ expensesPage }} من {{ expensesTotalPages }}</span>
          <UiButton variant="outline" size="sm" :disabled="expensesPage >= expensesTotalPages" @click="goToExpensesPage(expensesPage + 1)">
            التالي
          </UiButton>
        </div>
      </UiCard>

      <UiDialog
        v-model:open="expenseDialogOpen"
        title="إضافة مصروف للعميل"
        :description="statement.client.name"
      >
        <form @submit.prevent="addExpense">
          <div class="ui-field">
            <UiLabel html-for="cx-amount">المبلغ</UiLabel>
            <UiInput id="cx-amount" v-model="expenseForm.amount" type="number" step="0.01" min="0.01" required />
          </div>
          <div class="ui-field">
            <UiLabel html-for="cx-date">التاريخ</UiLabel>
            <UiInput id="cx-date" v-model="expenseForm.expense_date" type="date" required />
          </div>
          <div class="ui-field">
            <UiLabel html-for="cx-category">التصنيف الفرعي</UiLabel>
            <UiSelect id="cx-category" v-model="expenseForm.category" required>
              <option :value="null" disabled>اختر التصنيف الفرعي</option>
              <option v-for="c in lookups.categories" :key="c.id" :value="c.id">
                {{ c.main_category_name }} / {{ c.name }}
              </option>
            </UiSelect>
          </div>
          <div class="ui-field">
            <UiLabel html-for="cx-desc">الوصف</UiLabel>
            <UiTextarea id="cx-desc" v-model="expenseForm.description" :rows="3" required />
          </div>
          <p v-if="expenseError" class="ui-error">{{ expenseError }}</p>
          <div class="ui-dialog-footer">
            <UiButton type="submit" :disabled="expenseSaving">
              {{ expenseSaving ? 'جارٍ الحفظ…' : 'حفظ' }}
            </UiButton>
            <UiButton type="button" variant="outline" @click="expenseDialogOpen = false">إلغاء</UiButton>
          </div>
        </form>
      </UiDialog>
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
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
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
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
.section-head .section-title {
  margin: 0;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 0 0.5rem;
}
.row-link {
  cursor: pointer;
}
.row-link:hover {
  background: hsl(var(--muted) / 0.35);
}
</style>
