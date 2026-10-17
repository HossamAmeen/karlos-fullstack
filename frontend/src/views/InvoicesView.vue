<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import type { Invoice, InvoiceStatus, PaymentStatus } from '@/api/invoices'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { useAuthStore } from '@/stores/auth'
import { useInvoicesStore } from '@/stores/invoices'

const auth = useAuthStore()
const invoices = useInvoicesStore()
const router = useRouter()

const statusLabels: Record<InvoiceStatus, string> = {
  draft: 'مسودة',
  confirmed: 'مؤكدة',
  cancelled: 'ملغاة',
}

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

async function load() {
  try {
    await invoices.fetchAll()
  } catch (err) {
    await handleAuthError(err)
  }
}

async function onSearch() {
  await load()
}

function openCreate() {
  void router.push({ name: 'invoice-new' })
}

function openInvoice(invoice: Invoice) {
  void router.push({ name: 'invoice-edit', params: { id: invoice.id } })
}

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>الفواتير</h1>
        <p class="muted">إنشاء ومتابعة فواتير العملاء</p>
      </div>
      <UiButton @click="openCreate">فاتورة جديدة</UiButton>
    </header>

    <UiCard>
      <div class="toolbar">
        <UiInput
          v-model="invoices.search"
          placeholder="بحث بالرقم أو العميل..."
          @keyup.enter="onSearch"
        />
        <UiSelect v-model="invoices.statusFilter" @change="onSearch">
          <option value="">كل الحالات</option>
          <option value="draft">مسودة</option>
          <option value="confirmed">مؤكدة</option>
          <option value="cancelled">ملغاة</option>
        </UiSelect>
        <UiButton variant="outline" @click="onSearch">بحث</UiButton>
      </div>

      <p v-if="invoices.loading" class="muted">جاري التحميل...</p>
      <p v-else-if="invoices.error" class="error">{{ invoices.error }}</p>

      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>الرقم</th>
              <th>العميل</th>
              <th>التاريخ</th>
              <th>الحالة</th>
              <th>الإجمالي</th>
              <th>المدفوع</th>
              <th>المتبقي</th>
              <th>الدفع</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="invoice in invoices.items"
              :key="invoice.id"
              class="row-link"
              @click="openInvoice(invoice)"
            >
              <td>{{ invoice.number }}</td>
              <td>{{ invoice.client_name }}</td>
              <td>{{ invoice.issue_date }}</td>
              <td>
                <span class="pill" :data-status="invoice.status">
                  {{ statusLabels[invoice.status] }}
                </span>
              </td>
              <td>{{ invoice.total }}</td>
              <td>{{ invoice.amount_paid }}</td>
              <td>{{ invoice.amount_remaining }}</td>
              <td>
                <div class="payment-cell">
                  <span>{{ paymentLabels[invoice.payment_status] }}</span>
                  <span v-if="invoice.is_settled" class="settled-badge" title="تمت التسوية">
                    ✓
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!invoices.items.length" class="muted empty">لا توجد فواتير بعد.</p>
      </div>
    </UiCard>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
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
.toolbar {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (min-width: 768px) {
  .toolbar {
    grid-template-columns: 1fr 10rem auto;
    align-items: center;
  }
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  text-align: right;
  padding: 0.75rem 0.5rem;
  border-bottom: 1px solid hsl(var(--border));
  white-space: nowrap;
}
.row-link {
  cursor: pointer;
}
.row-link:hover {
  background: hsl(var(--muted) / 0.35);
}
.pill {
  display: inline-flex;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  background: hsl(var(--muted));
}
.pill[data-status='confirmed'] {
  background: hsl(142 40% 90%);
  color: hsl(142 50% 25%);
}
.pill[data-status='cancelled'] {
  background: hsl(0 40% 92%);
  color: hsl(0 45% 35%);
}
.empty {
  padding: 1rem 0;
}
.payment-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.settled-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1rem;
  height: 1.1rem;
  background: hsl(142 60% 45%);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: bold;
}
</style>
