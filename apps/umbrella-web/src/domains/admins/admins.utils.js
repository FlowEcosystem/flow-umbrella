import { getRoleLabel } from '@/app/access/rbac'
import { buildValidationState, formatRelativeDate, normalizeOptionalText } from '@/shared/lib/domain-ui'

export const ADMIN_ROLE_OPTIONS = Object.freeze([
  { label: getRoleLabel('superadmin'), value: 'superadmin' },
  { label: getRoleLabel('admin'), value: 'admin' },
  { label: getRoleLabel('viewer'), value: 'viewer' },
])

export { buildValidationState, normalizeOptionalText }

export function formatLastLogin(value) {
  if (!value) return { text: 'Ни разу не входил', muted: true }
  return formatRelativeDate(value)
}

export function getAdminInitials(admin) {
  const source = admin?.full_name || admin?.email || ''
  return source
    .split(/[\s@._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}
