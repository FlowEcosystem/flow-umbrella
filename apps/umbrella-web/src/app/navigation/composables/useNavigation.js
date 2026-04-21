import { getAccessibleNavigation, getQuickActions } from '@/app/navigation/navigation.config'
import { useAuthStore } from '@/domains/auth/store'

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
