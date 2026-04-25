import { servicesApi } from '@/domains/policies/api'

export const useServicesStore = defineStore('services', () => {
  const items     = ref([])
  const isLoading = ref(false)
  const error     = ref(null)

  // Группировка по категориям: [{ label, services: [...] }]
  const grouped = computed(() => {
    const map = new Map()
    for (const s of items.value) {
      if (!map.has(s.category)) map.set(s.category, [])
      map.get(s.category).push(s)
    }
    return [...map.entries()].map(([label, services]) => ({ label, services }))
  })

  async function fetch() {
    isLoading.value = true
    error.value = null
    try {
      // Загружаем все сервисы постранично (лимит API — 200)
      let offset = 0
      const all = []
      while (true) {
        const data = await servicesApi.list({ limit: 200, offset })
        all.push(...data.items)
        if (all.length >= data.meta.total) break
        offset += 200
      }
      items.value = all
    } catch (err) {
      error.value = err.message ?? 'Ошибка загрузки сервисов'
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload) {
    const data = await servicesApi.create(payload)
    items.value.push(data)
    return data
  }

  async function update(id, payload) {
    const data = await servicesApi.update(id, payload)
    const idx = items.value.findIndex(s => s.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function remove(id) {
    await servicesApi.delete(id)
    items.value = items.value.filter(s => s.id !== id)
  }

  return { items, grouped, isLoading, error, fetch, create, update, remove }
})
