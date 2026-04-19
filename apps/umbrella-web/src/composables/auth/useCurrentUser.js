import { useAuthStore } from '@/stores/auth.store'

export function useCurrentUser() {
  const authStore = useAuthStore()

  return {
    user: computed(() => authStore.user),
    role: computed(() => authStore.role),
    roleLabel: computed(() => authStore.roleLabel),
    isAuthenticated: computed(() => authStore.isAuthenticated),
  }
}
