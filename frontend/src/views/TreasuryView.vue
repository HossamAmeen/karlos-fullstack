<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import ClientPicker from '@/components/ClientPicker.vue'
import DepositDialog from '@/components/DepositDialog.vue'
import ExpenseDialog from '@/components/ExpenseDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import { useAuthStore } from '@/stores/auth'
import { useTreasuryStore, type TreasuryTab } from '@/stores/treasury'
import { paymentMethodLabels } from '@/utils/paymentMethods'

const auth = useAuthStore()
const treasury = useTreasuryStore()
const router = useRouter()

const clientPickerKey = ref(0)
const depositOpen = ref(false)
const expenseOpen = ref(false)
const pickedClientId = computed({
  get: () => treasury.clientId ?? '',
  set: (value: number | string) => {
    treasury.clientId = value === '' ? null : Number(value)
    void applyFilters()
  },
})

async function load() {
  try {
    await treasury.fetchAll()
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      auth.logout()
      await router.push({ name: 'login' })
    }
  }
}

async function applyFilters() {
  treasury.page = 1
  await load()
}

async function setTab(tab: TreasuryTab) {
  if (treasury.tab === tab) return
  treasury.tab = tab
  await applyFilters()
}

async function clearFilters() {
  treasury.reset()
  clientPickerKey.value++
  await load()
}

const totalPages = computed(() =>
  Math.max(1, Math.ceil(treasury.totalCount / treasury.pageSize)),
)

async function goToPage(p: number) {
  if (p < 1 || p > totalPages.value || p === treasury.page) return
  treasury.page = p
  await load()
}

function money(value: number) {
  return value.toFixed(2)
}

const hasFilters = computed(
  () => !!(treasury.startDate || treasury.endDate || treasury.clientId != null),
)

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>الخزنة</h1>
        <p class="muted">مدفوعات العملاء والمصروفات</p>
      </div>
      <div class="header-actions">
        <UiButton @click="depositOpen = true">إضافة دفع</UiButton>
        <UiButton variant="outline" @click="expenseOpen = true">إضافة مصروف</UiButton>
      </div>
    </header>

    <DepositDialog v-model:open="depositOpen" @saved="load" />
    <ExpenseDialog v-model:open="expenseOpen" @saved="load" />

    <div class="summary-cards">
      <UiCard class="stat-card in">
        <p class="stat-label">إجمالي المدفوعات</p>
        <p class="stat in">{{ money(treasury.totalPayments) }}</p>
      </UiCard>
      <UiCard class="stat-card out">
        <p class="stat-label">إجمالي المصروفات</p>
        <p class="stat out">{{ money(treasury.totalExpenses) }}</p>
      </UiCard>
      <UiCard class="stat-card net" :class="treasury.net < 0 ? 'out' : 'in'">
        <p class="stat-label">الصافي في الخزنة</p>
        <p class="stat" :class="treasury.net < 0 ? 'out' : 'in'">{{ money(treasury.net) }}</p>
      </UiCard>
    </div>

    <UiCard>
      <div class="tab-buttons" role="tablist">
        <button
          type="button"
          role="tab"
          class="tab-btn"
          :class="{ active: treasury.tab === 'payments' }"
          :aria-selected="treasury.tab === 'payments'"
          @click="setTab('payments')"
        >
          المدفوعات
        </button>
        <button
          type="button"
          role="tab"
          class="tab-btn"
          :class="{ active: treasury.tab === 'expenses' }"
          :aria-selected="treasury.tab === 'expenses'"
          @click="setTab('expenses')"
        >
          المصروفات
        </button>
      </div>

      <div class="filters">
        <div>
          <UiLabel>العميل</UiLabel>
          <ClientPicker :key="clientPickerKey" v-model="pickedClientId" />
        </div>
        <div>
          <UiLabel>من تاريخ</UiLabel>
          <UiInput v-model="treasury.startDate" type="date" @change="applyFilters" />
        </div>
        <div>
          <UiLabel>إلى تاريخ</UiLabel>
          <UiInput v-model="treasury.endDate" type="date" @change="applyFilters" />
        </div>
        <UiButton v-if="hasFilters" variant="outline" @click="clearFilters">مسح الفلاتر</UiButton>
      </div>

      <p v-if="treasury.error" class="error">{{ treasury.error }}</p>
      <p v-else-if="treasury.loading" class="muted">جاري التحميل...</p>

      <div v-else class="table-wrap">
        <table v-if="treasury.tab === 'payments'">
          <thead>
            <tr>
              <th>#</th>
              <th>التاريخ</th>
              <th>العميل</th>
              <th>الفاتورة</th>
              <th>المبلغ</th>
              <th>طريقة الدفع</th>
              <th>ملاحظات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in treasury.payments" :key="p.id">
              <td>{{ (treasury.page - 1) * treasury.pageSize + i + 1 }}</td>
              <td>{{ p.paid_at }}</td>
              <td>{{ p.client_name }}</td>
              <td>{{ p.invoice_number || 'وديعة عامة' }}</td>
              <td class="amount in">{{ p.amount }}</td>
              <td><span class="method-pill" :data-method="p.method">{{ paymentMethodLabels[p.method] ?? p.method }}</span></td>
              <td class="notes">{{ p.notes || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <table v-else>
          <thead>
            <tr>
              <th>#</th>
              <th>التاريخ</th>
              <th>التصنيف</th>
              <th>العميل</th>
              <th>الوصف</th>
              <th>المبلغ</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(e, i) in treasury.expenses" :key="e.id">
              <td>{{ (treasury.page - 1) * treasury.pageSize + i + 1 }}</td>
              <td>{{ e.expense_date }}</td>
              <td>{{ e.main_category_name }} / {{ e.category_name }}</td>
              <td>{{ e.client_name || '—' }}</td>
              <td class="notes">{{ e.description || '—' }}</td>
              <td class="amount out">{{ e.amount }}</td>
            </tr>
          </tbody>
        </table>
        <p
          v-if="!(treasury.tab === 'payments' ? treasury.payments : treasury.expenses).length"
          class="muted empty"
        >
          لا توجد بيانات.
        </p>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <UiButton variant="outline" size="sm" :disabled="treasury.page <= 1" @click="goToPage(treasury.page - 1)">
          السابق
        </UiButton>
        <span>صفحة {{ treasury.page }} من {{ totalPages }} ({{ treasury.totalCount }})</span>
        <UiButton variant="outline" size="sm" :disabled="treasury.page >= totalPages" @click="goToPage(treasury.page + 1)">
          التالي
        </UiButton>
      </div>
    </UiCard>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
  min-width: 0;
}
.page > * {
  min-width: 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}
.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.page-header h1 {
  margin: 0;
  font-size: 1.5rem;
}
.muted {
  color: hsl(var(--muted-foreground));
  margin: 0.25rem 0 0;
}
.error {
  color: hsl(var(--destructive));
}
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
  gap: 1rem;
}
.stat-card {
  position: relative;
  overflow: hidden;
  border-top: 4px solid hsl(var(--border));
}
.stat-card.in {
  border-top-color: hsl(142 55% 40%);
}
.stat-card.out {
  border-top-color: hsl(0 60% 50%);
}
.stat-card.net {
  background: hsl(var(--muted) / 0.35);
}
.stat-label {
  margin: 0;
  font-size: 0.9rem;
  color: hsl(var(--muted-foreground));
}
.stat {
  margin: 0.4rem 0 0;
  font-size: 1.75rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.stat.in {
  color: hsl(142 50% 28%);
}
.stat.out {
  color: hsl(0 60% 40%);
}
.tab-buttons {
  display: inline-flex;
  padding: 0.25rem;
  gap: 0.25rem;
  margin-bottom: 1rem;
  background: hsl(var(--muted));
  border-radius: 0.75rem;
}
.tab-btn {
  min-width: 7.5rem;
  padding: 0.5rem 1.25rem;
  border: 0;
  border-radius: 0.55rem;
  background: transparent;
  color: hsl(var(--muted-foreground));
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}
.tab-btn:hover {
  color: hsl(var(--foreground));
}
.tab-btn.active {
  background: hsl(var(--background));
  color: hsl(var(--foreground));
  box-shadow: 0 1px 4px hsl(0 0% 0% / 0.12);
}
.filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  padding: 1rem;
  align-items: end;
  background: hsl(var(--muted) / 0.35);
  border: 1px solid hsl(var(--border));
  border-radius: 0.75rem;
}
.filters :deep(label),
.filters :deep(.ui-label) {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
}
@media (min-width: 768px) {
  .filters {
    grid-template-columns: 2fr 1fr 1fr auto;
  }
}
.table-wrap {
  overflow-x: auto;
  border: 1px solid hsl(var(--border));
  border-radius: 0.75rem;
}
table {
  width: 100%;
  border-collapse: collapse;
}
thead th {
  background: hsl(var(--muted) / 0.5);
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
  font-weight: 600;
}
th,
td {
  text-align: right;
  padding: 0.8rem 0.9rem;
  border-bottom: 1px solid hsl(var(--border));
  white-space: nowrap;
}
tbody tr:last-child td {
  border-bottom: 0;
}
tbody tr:hover {
  background: hsl(var(--muted) / 0.3);
}
.amount {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.amount.in {
  color: hsl(142 50% 28%);
}
.amount.out {
  color: hsl(0 60% 40%);
}
.notes {
  max-width: 18rem;
  overflow: hidden;
  text-overflow: ellipsis;
  color: hsl(var(--muted-foreground));
}
.method-pill {
  display: inline-flex;
  padding: 0.15rem 0.65rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  background: hsl(var(--muted));
}
.method-pill[data-method='instapay'] {
  background: hsl(262 70% 94%);
  color: hsl(262 55% 38%);
}
.method-pill[data-method='wallet'] {
  background: hsl(30 90% 91%);
  color: hsl(25 70% 35%);
}
.method-pill[data-method='cash'] {
  background: hsl(142 40% 90%);
  color: hsl(142 50% 25%);
}
.empty {
  padding: 1.5rem 0;
  text-align: center;
}
@media (max-width: 767px) {
  .tab-buttons {
    display: flex;
  }
  .tab-btn {
    flex: 1;
  }
  .header-actions {
    width: 100%;
  }
  .header-actions > * {
    flex: 1;
  }
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 0 0.5rem;
}
</style>
