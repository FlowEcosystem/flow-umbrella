import { authApi } from '@/api/auth.api'
import { setAccessToken } from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(null)
  const currentUser = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const ready = ref(false)
  let initializationPromise = null

  const isAuthenticated = computed(() => Boolean(accessToken.value && currentUser.value))

  function hasRole(roles = []) {
    if (!currentUser.value) return false
    if (!roles.length) return true
    const list = Array.isArray(roles) ? roles : [roles]
    return list.includes(currentUser.value.role)
  }

  async function fetchMe() {
    const data = await authApi.me()
    currentUser.value = data
  }

  async function login(email, password) {
    isLoading.value = true
    error.value = null
    try {
      const data = await authApi.login({ email, password })
      accessToken.value = data.access_token
      setAccessToken(data.access_token)
      await fetchMe()
    } catch (err) {
      error.value = err.message ?? 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // clear locally even if backend is unreachable
    } finally {
      accessToken.value = null
      currentUser.value = null
      setAccessToken(null)
    }
  }

  async function refresh() {
    if (initializationPromise) return initializationPromise

    initializationPromise = (async () => {
      try {
        const data = await authApi.refresh()
        accessToken.value = data.access_token
        setAccessToken(data.access_token)
        await fetchMe()
      } catch {
        accessToken.value = null
        currentUser.value = null
      } finally {
        ready.value = true
        initializationPromise = null
      }
    })()

    try {
      await initializationPromise
    } catch {
      // refresh handles state cleanup internally
    }
  }

  async function ensureInitialized() {
    if (ready.value) return
    await refresh()
  }

  return {
    accessToken,
    currentUser,
    isLoading,
    error,
    ready,
    isAuthenticated,
    hasRole,
    login,
    logout,
    fetchMe,
    refresh,
    ensureInitialized,
  }
})
