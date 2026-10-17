import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  createService,
  deleteService,
  listServices,
  updateService,
  type Service,
  type ServicePayload,
} from '@/api/services'
import { ApiError } from '@/api/client'

export const useServicesStore = defineStore('services', () => {
  const items = ref<Service[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const search = ref('')
  const categoryFilter = ref<number | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await listServices({
        search: search.value || undefined,
        service_category: categoryFilter.value ?? undefined,
      })
      items.value = data.results
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to load services'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(payload: ServicePayload) {
    const service = await createService(payload)
    items.value = [service, ...items.value.filter((s) => s.id !== service.id)]
    return service
  }

  async function update(id: number, payload: ServicePayload) {
    const service = await updateService(id, payload)
    items.value = items.value.map((s) => (s.id === id ? service : s))
    return service
  }

  async function remove(id: number) {
    await deleteService(id)
    items.value = items.value.filter((s) => s.id !== id)
  }

  return {
    items,
    loading,
    error,
    search,
    categoryFilter,
    fetchAll,
    create,
    update,
    remove,
  }
})
