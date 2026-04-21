import { agentsApi } from '@/domains/agents/api'

const DEFAULT_FILTERS = Object.freeze({
  status: [],
  os: null,
  search: '',
})

export const useAgentsStore = defineStore('agents', () => {
  const items = ref([])
  const total = ref(0)
  const limit = ref(50)
  const offset = ref(0)
  const filters = ref({ ...DEFAULT_FILTERS })
  const isLoading = ref(false)
  const error = ref(null)
  let activeFetchController = null
  let activeFetchId = 0

  async function fetch({ limit: l, offset: o } = {}) {
    const lim = l ?? limit.value
    const off = o ?? offset.value
    const fetchId = ++activeFetchId

    activeFetchController?.abort()
    activeFetchController = new AbortController()

    isLoading.value = true
    error.value = null
    try {
      const data = await agentsApi.list({
        limit: lim,
        offset: off,
        signal: activeFetchController.signal,
      })
      if (fetchId !== activeFetchId) return

      items.value = data.items
      total.value = data.meta.total
      limit.value = lim
      offset.value = off
    } catch (err) {
      if (err.message === 'canceled') {
        return
      }
      if (fetchId !== activeFetchId) return
      error.value = err
      throw err
    } finally {
      if (fetchId === activeFetchId) {
        isLoading.value = false
        activeFetchController = null
      }
    }
  }

  async function create(payload) {
    const data = await agentsApi.create(payload)
    await fetch({ limit: limit.value, offset: 0 })
    return data
  }

  async function update(id, patch) {
    const data = await agentsApi.update(id, patch)
    const idx = items.value.findIndex((item) => item.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function remove(id) {
    await agentsApi.remove(id)
    items.value = items.value.filter((item) => item.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  async function regenerateEnrollmentToken(id) {
    const data = await agentsApi.regenerateEnrollmentToken(id)
    const idx = items.value.findIndex((item) => item.id === id)
    if (idx !== -1) items.value[idx] = data.agent
    return data
  }

  return {
    items,
    total,
    limit,
    offset,
    filters,
    isLoading,
    error,
    fetch,
    create,
    update,
    remove,
    regenerateEnrollmentToken,
  }
})
