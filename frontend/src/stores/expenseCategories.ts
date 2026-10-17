import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  expenseCategoriesApi,
  expenseMainCategoriesApi,
  type ExpenseCategory,
  type ExpenseCategoryPayload,
  type ExpenseMainCategory,
  type ExpenseMainCategoryPayload,
} from '@/api/expenseCategories'

export const useExpenseCategoriesStore = defineStore('expenseCategories', () => {
  const mainCategories = ref<ExpenseMainCategory[]>([])
  const categories = ref<ExpenseCategory[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load<T>(target: { value: T[] }, fetcher: () => Promise<{ results: T[] }>) {
    loading.value = true
    error.value = null
    try {
      target.value = (await fetcher()).results
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to load data'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchMainCategories = () =>
    load(mainCategories, () => expenseMainCategoriesApi.list())
  const fetchCategories = (mainCategory?: number | null) =>
    load(categories, () =>
      expenseCategoriesApi.list({ main_category: mainCategory ?? undefined }),
    )

  async function createMainCategory(payload: ExpenseMainCategoryPayload) {
    await expenseMainCategoriesApi.create(payload)
    await fetchMainCategories()
  }
  async function updateMainCategory(id: number, payload: ExpenseMainCategoryPayload) {
    await expenseMainCategoriesApi.update(id, payload)
    await fetchMainCategories()
  }
  async function removeMainCategory(id: number) {
    await expenseMainCategoriesApi.remove(id)
    await fetchMainCategories()
  }

  async function createCategory(payload: ExpenseCategoryPayload) {
    await expenseCategoriesApi.create(payload)
  }
  async function updateCategory(id: number, payload: ExpenseCategoryPayload) {
    await expenseCategoriesApi.update(id, payload)
  }
  async function removeCategory(id: number) {
    await expenseCategoriesApi.remove(id)
  }

  return {
    mainCategories,
    categories,
    loading,
    error,
    fetchMainCategories,
    fetchCategories,
    createMainCategory,
    updateMainCategory,
    removeMainCategory,
    createCategory,
    updateCategory,
    removeCategory,
  }
})
