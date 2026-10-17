import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  createExpense,
  deleteExpense,
  getExpensesSummary,
  listExpenses,
  updateExpense,
  type Expense,
  type ExpensePayload,
  type ExpensesSummary,
} from '@/api/expenses'
import { ApiError } from '@/api/client'

export const useExpensesStore = defineStore('expenses', () => {
  const items = ref<Expense[]>([])
  const summary = ref<ExpensesSummary | null>(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Filters
  const search = ref('')
  const dateFilter = ref('')
  const startDateFilter = ref('')
  const endDateFilter = ref('')
  const categoryFilter = ref('')
  const serviceCategoryFilter = ref<number | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const params = {
        search: search.value || undefined,
        date: dateFilter.value || undefined,
        start_date: startDateFilter.value || undefined,
        end_date: endDateFilter.value || undefined,
        category: categoryFilter.value || undefined,
        service_category: serviceCategoryFilter.value ?? undefined,
      }
      
      const [listData, summaryData] = await Promise.all([
        listExpenses(params),
        getExpensesSummary(params)
      ])
      
      items.value = listData.results
      summary.value = summaryData
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to load expenses'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(payload: ExpensePayload) {
    const expense = await createExpense(payload)
    await fetchAll() // refresh to update summary and list sorting
    return expense
  }

  async function update(id: number, payload: ExpensePayload) {
    const expense = await updateExpense(id, payload)
    await fetchAll()
    return expense
  }

  async function remove(id: number) {
    await deleteExpense(id)
    await fetchAll()
  }

  return { 
    items, summary, loading, error, 
    search, dateFilter, startDateFilter, endDateFilter, categoryFilter, serviceCategoryFilter,
    fetchAll, create, update, remove 
  }
})
