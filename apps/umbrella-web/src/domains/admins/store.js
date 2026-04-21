import { adminsApi } from './api'

export const useAdminsStore = defineStore('admins', () => {
  const items = ref([])
  const total = ref(0)
  const limit = ref(50)
  const offset = ref(0)
  const isLoading = ref(false)
  const error = ref(null)

  async function fetch({ limit: l, offset: o } = {}) {
    const lim = l ?? limit.value
    const off = o ?? offset.value
    isLoading.value = true
    error.value = null
    try {
      const data = await adminsApi.list({ limit: lim, offset: off })
      items.value = data.items
      total.value = data.meta.total
      limit.value = lim
      offset.value = off
    } catch (err) {
      error.value = err
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload) {
    const data = await adminsApi.create(payload)
    await fetch({ limit: limit.value, offset: 0 })
    return data
  }

  async function update(id, patch) {
    const data = await adminsApi.update(id, patch)
    const idx = items.value.findIndex((item) => item.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function remove(id) {
    await adminsApi.remove(id)
    items.value = items.value.filter((item) => item.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  return { items, total, limit, offset, isLoading, error, fetch, create, update, remove }
})
