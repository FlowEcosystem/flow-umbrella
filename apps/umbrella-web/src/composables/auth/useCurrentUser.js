import { useAuthStore } from '@/stores/auth.store'
import { getRoleLabel } from '@/config/rbac'

export function useCurrentUser() {
  const authStore = useAuthStore()

  return {
    user: computed(() => authStore.currentUser),
    role: computed(() => authStore.currentUser?.role ?? null),
    roleLabel: computed(() => getRoleLabel(authStore.currentUser?.role)),
    isAuthenticated: computed(() => authStore.isAuthenticated),
  }
}
