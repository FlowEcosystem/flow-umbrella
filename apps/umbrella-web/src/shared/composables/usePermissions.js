import { useAuthStore } from '@/domains/auth/store'

export function usePermissions() {
  const auth = useAuthStore()

  const role         = computed(() => auth.currentUser?.role ?? null)
  const canWrite     = computed(() => role.value === 'admin' || role.value === 'superadmin')
  const isSuperAdmin = computed(() => role.value === 'superadmin')

  return { role, canWrite, isSuperAdmin }
}
