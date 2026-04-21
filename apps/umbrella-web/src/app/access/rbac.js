import { roleHasCapability } from './capabilities'

export const ROLES = Object.freeze({
  SUPERADMIN: 'superadmin',
  ADMIN: 'admin',
  VIEWER: 'viewer',
})

export const ROLE_LABELS = Object.freeze({
  [ROLES.SUPERADMIN]: 'Суперадминистратор',
  [ROLES.ADMIN]: 'Администратор',
  [ROLES.VIEWER]: 'Наблюдатель',
})

export const ALL_ROLES = Object.freeze(Object.values(ROLES))

export function resolveRole(role) {
  if (!role) return null
  return ALL_ROLES.includes(role) ? role : null
}

export function getRoleLabel(role) {
  return ROLE_LABELS[role] ?? 'Пользователь'
}

export function hasRole(userRole, roles = []) {
  if (!roles.length) return true
  return roles.includes(userRole)
}

export function canAccess(userRole, requiredRoles = []) {
  return hasRole(userRole, requiredRoles)
}

export function can(userRole, capability) {
  return roleHasCapability(userRole, capability)
}
