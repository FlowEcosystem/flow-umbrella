import { agentsApi } from '@/domains/agents/api'

export const useAgentsStore = defineStore('agents', () => {
  const items     = ref([])
  const total     = ref(0)
  const isLoading = ref(false)
  const error     = ref(null)

  async function fetch() {
    isLoading.value = true
    error.value = null
    try {
      const data = await agentsApi.list({ limit: 200, offset: 0 })
      items.value = data.items
      total.value = data.meta.total
    } catch (err) {
      error.value = err.message ?? 'Ошибка загрузки'
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload) {
    return agentsApi.create(payload)
  }

  async function update(id, payload) {
    const data = await agentsApi.update(id, payload)
    const idx = items.value.findIndex(a => a.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function remove(id) {
    await agentsApi.delete(id)
    items.value = items.value.filter(a => a.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  async function regenerateToken(id) {
    return agentsApi.regenerateToken(id)
  }

  return { items, total, isLoading, error, fetch, create, update, remove, regenerateToken }
})
