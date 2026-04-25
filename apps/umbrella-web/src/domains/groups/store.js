import { groupsApi } from '@/domains/groups/api'

export const useGroupsStore = defineStore('groups', () => {
  const items     = ref([])
  const total     = ref(0)
  const isLoading = ref(false)
  const error     = ref(null)

  async function fetch() {
    isLoading.value = true
    error.value = null
    try {
      const data = await groupsApi.list({ limit: 200, offset: 0 })
      items.value = data.items
      total.value = data.meta.total
    } catch (err) {
      error.value = err.message ?? 'Ошибка загрузки'
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload) {
    const data = await groupsApi.create(payload)
    items.value.unshift(data)
    total.value += 1
    return data
  }

  async function update(id, payload) {
    const data = await groupsApi.update(id, payload)
    const idx = items.value.findIndex(g => g.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function remove(id) {
    await groupsApi.delete(id)
    items.value = items.value.filter(g => g.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  function patchCount(id, delta) {
    const g = items.value.find(g => g.id === id)
    if (g) g.agents_count = Math.max(0, (g.agents_count ?? 0) + delta)
  }

  return { items, total, isLoading, error, fetch, create, update, remove, patchCount }
})
