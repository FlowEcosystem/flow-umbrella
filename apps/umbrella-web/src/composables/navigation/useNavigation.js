import { getAccessibleNavigation, getQuickActions } from '@/config/navigation'
import { useAuthStore } from '@/stores/auth.store'

export function useNavigation() {
  const authStore = useAuthStore()

  const role = computed(() => authStore.currentUser?.role ?? null)
  const sections = computed(() => getAccessibleNavigation(role.value))
  const quickActions = computed(() => getQuickActions(role.value))

  return {
    sections,
    quickActions,
  }
}
