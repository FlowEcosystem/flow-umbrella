import { useAuthStore } from '@/domains/auth/store'

export function useCurrentUser() {
  const store = useAuthStore()
  return {
    user:            computed(() => store.currentUser),
    isAuthenticated: computed(() => store.isAuthenticated),
  }
}
