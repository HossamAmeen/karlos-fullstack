import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  createClient,
  deleteClient,
  listClients,
  updateClient,
  type Client,
  type ClientPayload,
} from '@/api/clients'
import { ApiError } from '@/api/client'

export const useClientsStore = defineStore('clients', () => {
  const items = ref<Client[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const search = ref('')

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await listClients({ search: search.value || undefined })
      items.value = data.results
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to load clients'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(payload: ClientPayload) {
    const client = await createClient(payload)
    items.value = [client, ...items.value.filter((c) => c.id !== client.id)]
    return client
  }

  async function update(id: number, payload: ClientPayload) {
    const client = await updateClient(id, payload)
    items.value = items.value.map((c) => (c.id === id ? client : c))
    return client
  }

  async function remove(id: number) {
    await deleteClient(id)
    items.value = items.value.filter((c) => c.id !== id)
  }

  return { items, loading, error, search, fetchAll, create, update, remove }
})
