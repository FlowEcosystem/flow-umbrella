import { policiesApi } from '@/domains/policies/api'

export const usePoliciesStore = defineStore('policies', () => {
  const items     = ref([])
  const total     = ref(0)
  const isLoading = ref(false)
  const error     = ref(null)

  async function fetch() {
    isLoading.value = true
    error.value = null
    try {
      const data = await policiesApi.list({ limit: 200, offset: 0 })
      items.value = data.items
      total.value = data.meta.total
    } catch (err) {
      error.value = err.message ?? 'Ошибка загрузки'
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload) {
    const data = await policiesApi.create(payload)
    items.value.unshift(data)
    total.value += 1
    return data
  }

  async function update(id, payload) {
    const data = await policiesApi.update(id, payload)
    const idx = items.value.findIndex(p => p.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function remove(id) {
    await policiesApi.delete(id)
    items.value = items.value.filter(p => p.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  return { items, total, isLoading, error, fetch, create, update, remove }
})
