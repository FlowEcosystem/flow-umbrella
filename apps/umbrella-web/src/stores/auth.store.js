import { sessionApi } from '@/api/session.api'
import { getRoleLabel, getRolePermissions, hasPermission, hasSomeRole, resolveRole } from '@/config/rbac'

function normalizeSession(payload) {
  if (!payload?.user) {
    return null
  }

  const role = resolveRole(payload.user.role ?? payload.role)

  if (!role) {
    return null
  }

  const fullName =
    payload.user.fullName ||
    [payload.user.lastName, payload.user.firstName].filter(Boolean).join(' ')

  return {
    user: {
      id: payload.user.id ?? null,
      firstName: payload.user.firstName ?? '',
      lastName: payload.user.lastName ?? '',
      fullName: fullName || payload.user.email || 'Пользователь',
      email: payload.user.email ?? '',
      avatarUrl: payload.user.avatarUrl ?? '',
      branchName: payload.user.branchName ?? '',
      groupName: payload.user.groupName ?? '',
    },
    role,
    permissions: [...new Set([...(payload.permissions ?? []), ...getRolePermissions(role)])],
  }
}

export const useAuthStore = defineStore('auth', () => {
  const ready = ref(false)
  const loading = ref(false)
  const error = ref('')
  const session = ref(null)
  const bootstrapPromise = ref(null)

  const user = computed(() => session.value?.user ?? null)
  const role = computed(() => session.value?.role ?? null)
  const permissions = computed(() => session.value?.permissions ?? [])
  const isAuthenticated = computed(() => Boolean(user.value && role.value))
  const roleLabel = computed(() => getRoleLabel(role.value))
  const displayName = computed(() => user.value?.fullName ?? 'Гость')

  function applySession(payload) {
    session.value = normalizeSession(payload)
  }

  function clearSession() {
    session.value = null
  }

  async function bootstrap(force = false) {
    if (loading.value && bootstrapPromise.value) {
      return bootstrapPromise.value
    }

    if (ready.value && !force) {
      return session.value
    }

    loading.value = true
    error.value = ''

    const request = sessionApi
      .fetchCurrentSession()
      .then((payload) => {
        applySession(payload)
        return session.value
      })
      .catch((err) => {
        clearSession()
        error.value = err?.message ?? 'Не удалось загрузить сессию'
        return null
      })
      .finally(() => {
        loading.value = false
        ready.value = true
        bootstrapPromise.value = null
      })

    bootstrapPromise.value = request
    return request
  }

  async function ensureInitialized() {
    if (ready.value) {
      return session.value
    }

    return bootstrap()
  }

  async function logout() {
    try {
      await sessionApi.logout()
    } catch {
      // Сессию очищаем локально даже если backend недоступен.
    } finally {
      clearSession()
      ready.value = true
    }
  }

  function hasRole(roles = []) {
    return hasSomeRole(role.value, roles)
  }

  function can(permission) {
    return hasPermission(role.value, permission, permissions.value)
  }

  return {
    ready,
    loading,
    error,
    session,
    user,
    role,
    permissions,
    isAuthenticated,
    roleLabel,
    displayName,
    applySession,
    clearSession,
    bootstrap,
    ensureInitialized,
    logout,
    hasRole,
    can,
  }
})
