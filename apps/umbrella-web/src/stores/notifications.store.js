import { notificationsApi } from '@/api/notifications.api'
import { useAuthStore } from '@/stores/auth.store'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref('')

  const unreadCount = computed(() => notifications.value.filter((x) => !x.read).length)

  async function fetchLatest() {
    if (loading.value) return

    const authStore = useAuthStore()

    if (!authStore.isAuthenticated) {
      notifications.value = []
      loaded.value = true
      return
    }

    loading.value = true
    error.value = ''

    try {
      notifications.value = await notificationsApi.fetchLatest()
      loaded.value = true
    } catch (err) {
      notifications.value = []
      error.value = err?.message ?? 'Не удалось загрузить уведомления'
    } finally {
      loading.value = false
    }
  }

  async function remove(id) {
    const backup = [...notifications.value]
    notifications.value = notifications.value.filter((x) => x.id !== id)

    try {
      await notificationsApi.remove(id)
    } catch (e) {
      notifications.value = backup
      throw e
    }
  }

  async function markRead(id) {
    const n = notifications.value.find((x) => x.id === id)
    if (!n || n.read) return

    const prev = n.read
    n.read = true

    try {
      await notificationsApi.markRead(id)
    } catch (e) {
      n.read = prev
      throw e
    }
  }

  async function markAllRead() {
    const backup = notifications.value.map((x) => ({ ...x }))
    notifications.value = notifications.value.map((x) => ({ ...x, read: true }))

    try {
      await notificationsApi.markAllRead()
    } catch (e) {
      notifications.value = backup
      throw e
    }
  }

  async function clear() {
    const backup = [...notifications.value]
    notifications.value = []

    try {
      await notificationsApi.clear()
    } catch (e) {
      notifications.value = backup
      throw e
    }
  }

  function reset() {
    notifications.value = []
    loaded.value = false
    error.value = ''
  }

  return {
    notifications,
    loading,
    loaded,
    error,
    unreadCount,
    fetchLatest,
    remove,
    markRead,
    markAllRead,
    clear,
    reset,
  }
})
