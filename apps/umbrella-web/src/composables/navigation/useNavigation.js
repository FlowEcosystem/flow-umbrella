import { getAccessibleNavigation, getQuickActions } from '@/config/navigation'
import { useAuthStore } from '@/stores/auth.store'

export function useNavigation() {
  const authStore = useAuthStore()

  const sections = computed(() => getAccessibleNavigation(authStore.role))
  const quickActions = computed(() => getQuickActions(authStore.role))

  return {
    sections,
    quickActions,
  }
}
