import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  createServiceCategory,
  deleteServiceCategory,
  listServiceCategories,
  updateServiceCategory,
  type ServiceCategory,
  type ServiceCategoryPayload,
} from '@/api/serviceCategories'
import { ApiError } from '@/api/client'

export const useServiceCategoriesStore = defineStore('serviceCategories', () => {
  const items = ref<ServiceCategory[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const search = ref('')

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await listServiceCategories({ search: search.value || undefined })
      items.value = data.results
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to load service categories'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(payload: ServiceCategoryPayload) {
    const category = await createServiceCategory(payload)
    items.value = [category, ...items.value.filter((c) => c.id !== category.id)]
    return category
  }

  async function update(id: number, payload: ServiceCategoryPayload) {
    const category = await updateServiceCategory(id, payload)
    items.value = items.value.map((c) => (c.id === id ? category : c))
    return category
  }

  async function remove(id: number) {
    await deleteServiceCategory(id)
    items.value = items.value.filter((c) => c.id !== id)
  }

  return { items, loading, error, search, fetchAll, create, update, remove }
})
