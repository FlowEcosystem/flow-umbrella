import { authApi } from '@/domains/auth/api'
import { setAccessToken } from '@/app/api/http'

export const useAuthStore = defineStore('auth', () => {
  const accessToken  = ref(null)
  const currentUser  = ref(null)
  const isLoading    = ref(false)
  const error        = ref(null)
  const ready        = ref(false)
  let   initPromise  = null

  const isAuthenticated = computed(() => Boolean(accessToken.value && currentUser.value))

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

  async function updateProfile(fields) {
    const data = await authApi.updateProfile(fields)
    currentUser.value = data
    return data
  }

  async function changePassword(current_password, new_password) {
    await authApi.changePassword({ current_password, new_password })
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // очищаем локально, даже если сервер недоступен
    } finally {
      accessToken.value = null
      currentUser.value = null
      setAccessToken(null)
    }
  }

  async function refresh() {
    if (initPromise) return initPromise
    initPromise = (async () => {
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
        initPromise = null
      }
    })()
    await initPromise
  }

  async function ensureInitialized() {
    if (ready.value) return
    await refresh()
  }

  return {
    currentUser,
    isLoading,
    error,
    ready,
    isAuthenticated,
    login,
    logout,
    refresh,
    ensureInitialized,
    updateProfile,
    changePassword,
  }
})
