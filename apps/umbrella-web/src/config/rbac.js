export const ROLES = Object.freeze({
  STUDENT: 'student',
  TEACHER: 'teacher',
  MANAGER: 'manager',
  DIRECTOR: 'director',
})

export const ROLE_LABELS = Object.freeze({
  [ROLES.STUDENT]: 'Студент',
  [ROLES.TEACHER]: 'Преподаватель',
  [ROLES.MANAGER]: 'Менеджер учебного процесса',
  [ROLES.DIRECTOR]: 'Директор',
})

export const PERMISSIONS = Object.freeze({
  SCHEDULE_VIEW_OWN: 'schedule:view:own',
  SCHEDULE_MANAGE: 'schedule:manage',
  HOMEWORK_VIEW_OWN: 'homework:view:own',
  HOMEWORK_SUBMIT_OWN: 'homework:submit:own',
  HOMEWORK_PUBLISH: 'homework:publish',
  HOMEWORK_REVIEW: 'homework:review',
  GRADES_VIEW_OWN: 'grades:view:own',
  GRADES_MANAGE_GROUP: 'grades:manage:group',
  MATERIALS_VIEW: 'materials:view',
  MATERIALS_MANAGE: 'materials:manage',
  GROUPS_VIEW_ASSIGNED: 'groups:view:assigned',
  GROUPS_MANAGE: 'groups:manage',
  STUDENTS_VIEW: 'students:view',
  USERS_MANAGE: 'users:manage',
  DISCIPLINES_MANAGE: 'disciplines:manage',
  REPORTS_VIEW_BRANCH: 'reports:view:branch',
  REPORTS_VIEW_GLOBAL: 'reports:view:global',
  IMPERSONATE: 'impersonate',
  ACCESS_MANAGE: 'access:manage',
  STATS_VIEW_OWN: 'stats:view:own',
  STATS_VIEW_GROUP: 'stats:view:group',
})

export const ALL_ROLES = Object.freeze(Object.values(ROLES))

export const ROLE_PERMISSIONS = Object.freeze({
  [ROLES.STUDENT]: [
    PERMISSIONS.SCHEDULE_VIEW_OWN,
    PERMISSIONS.HOMEWORK_VIEW_OWN,
    PERMISSIONS.HOMEWORK_SUBMIT_OWN,
    PERMISSIONS.GRADES_VIEW_OWN,
    PERMISSIONS.MATERIALS_VIEW,
    PERMISSIONS.STATS_VIEW_OWN,
  ],
  [ROLES.TEACHER]: [
    PERMISSIONS.SCHEDULE_VIEW_OWN,
    PERMISSIONS.HOMEWORK_PUBLISH,
    PERMISSIONS.HOMEWORK_REVIEW,
    PERMISSIONS.GRADES_MANAGE_GROUP,
    PERMISSIONS.MATERIALS_VIEW,
    PERMISSIONS.MATERIALS_MANAGE,
    PERMISSIONS.GROUPS_VIEW_ASSIGNED,
    PERMISSIONS.STUDENTS_VIEW,
    PERMISSIONS.STATS_VIEW_GROUP,
  ],
  [ROLES.MANAGER]: [
    PERMISSIONS.SCHEDULE_MANAGE,
    PERMISSIONS.HOMEWORK_REVIEW,
    PERMISSIONS.GRADES_MANAGE_GROUP,
    PERMISSIONS.MATERIALS_MANAGE,
    PERMISSIONS.GROUPS_MANAGE,
    PERMISSIONS.STUDENTS_VIEW,
    PERMISSIONS.USERS_MANAGE,
    PERMISSIONS.DISCIPLINES_MANAGE,
    PERMISSIONS.REPORTS_VIEW_BRANCH,
    PERMISSIONS.IMPERSONATE,
  ],
  [ROLES.DIRECTOR]: [
    PERMISSIONS.SCHEDULE_MANAGE,
    PERMISSIONS.HOMEWORK_REVIEW,
    PERMISSIONS.GRADES_MANAGE_GROUP,
    PERMISSIONS.MATERIALS_MANAGE,
    PERMISSIONS.GROUPS_MANAGE,
    PERMISSIONS.STUDENTS_VIEW,
    PERMISSIONS.USERS_MANAGE,
    PERMISSIONS.DISCIPLINES_MANAGE,
    PERMISSIONS.REPORTS_VIEW_BRANCH,
    PERMISSIONS.REPORTS_VIEW_GLOBAL,
    PERMISSIONS.IMPERSONATE,
    PERMISSIONS.ACCESS_MANAGE,
  ],
})

export function resolveRole(role) {
  if (!role) return null

  return ALL_ROLES.includes(role) ? role : null
}

export function getRoleLabel(role) {
  return ROLE_LABELS[role] ?? 'Пользователь'
}

export function getRolePermissions(role) {
  return ROLE_PERMISSIONS[role] ?? []
}

export function hasPermission(role, permission, scopedPermissions = []) {
  if (!permission) return true

  const permissions = new Set([...getRolePermissions(role), ...scopedPermissions])
  return permissions.has(permission)
}

export function hasSomeRole(role, roles = []) {
  if (!roles.length) return true
  return roles.includes(role)
}
