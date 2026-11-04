import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  getExpensesSummary,
  listExpenses,
  type Expense,
  type ExpensesSummary,
} from '@/api/expenses'
import {
  getPaymentsSummary,
  listPayments,
  type PaymentRow,
  type PaymentsSummary,
} from '@/api/payments'

export type TreasuryTab = 'payments' | 'expenses'

export const useTreasuryStore = defineStore('treasury', () => {
  const tab = ref<TreasuryTab>('payments')
  const startDate = ref('')
  const endDate = ref('')
  const clientId = ref<number | null>(null)

  const pageSize = 25
  const page = ref(1)
  const totalCount = ref(0)
  const payments = ref<PaymentRow[]>([])
  const expenses = ref<Expense[]>([])
  const paymentsSummary = ref<PaymentsSummary | null>(null)
  const expensesSummary = ref<ExpensesSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const totalPayments = computed(() => Number(paymentsSummary.value?.total_payments ?? 0))
  const totalExpenses = computed(() => Number(expensesSummary.value?.total_expenses ?? 0))
  const net = computed(() => totalPayments.value - totalExpenses.value)

  function filters() {
    return {
      client: clientId.value ?? undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
    }
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    const f = filters()
    const offset = (page.value - 1) * pageSize
    try {
      const [pSummary, eSummary, list] = await Promise.all([
        getPaymentsSummary(f),
        getExpensesSummary(f),
        tab.value === 'payments'
          ? listPayments({ ...f, limit: pageSize, offset })
          : listExpenses({ ...f, limit: pageSize, offset }),
      ])
      paymentsSummary.value = pSummary
      expensesSummary.value = eSummary
      totalCount.value = list.count
      const lastPage = Math.max(1, Math.ceil(list.count / pageSize))
      if (page.value > lastPage) {
        page.value = lastPage
        return fetchAll()
      }
      if (tab.value === 'payments') payments.value = list.results as PaymentRow[]
      else expenses.value = list.results as Expense[]
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'فشل تحميل الخزنة'
      throw err
    } finally {
      loading.value = false
    }
  }

  function reset() {
    startDate.value = ''
    endDate.value = ''
    clientId.value = null
    page.value = 1
  }

  return {
    tab,
    startDate,
    endDate,
    clientId,
    page,
    pageSize,
    totalCount,
    payments,
    expenses,
    paymentsSummary,
    expensesSummary,
    totalPayments,
    totalExpenses,
    net,
    loading,
    error,
    fetchAll,
    reset,
  }
})
