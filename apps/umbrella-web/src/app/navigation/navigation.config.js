import { roleHasCapability } from '@/app/access/capabilities'

export const navigationSections = Object.freeze([
  {
    key: 'workspace',
    label: 'Рабочая область',
    items: [
      {
        to: '/',
        label: 'Обзор',
        tooltip: 'Обзор',
        icon: 'LayoutGrid',
        exact: true,
        capability: null,
      },
      {
        to: '/admins',
        label: 'Администраторы',
        tooltip: 'Администраторы',
        icon: 'Users',
        exact: false,
        capability: 'admins:read',
      },
      {
        to: '/agents',
        label: 'Агенты',
        tooltip: 'Агенты',
        icon: 'Monitor',
        exact: false,
        capability: 'agents:read',
      },
      {
        to: '/groups',
        label: 'Группы',
        tooltip: 'Группы',
        icon: 'MapPinned',
        exact: false,
        capability: 'groups:read',
      },
    ],
  },
  {
    key: 'system',
    label: null,
    bottom: true,
    items: [
      {
        to: '/settings',
        label: 'Настройки',
        tooltip: 'Настройки',
        icon: 'Settings',
        exact: false,
        capability: 'self:read',
      },
    ],
  },
])

export function getAccessibleNavigation(role) {
  return navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (!item.capability) return true
        try { return roleHasCapability(role, item.capability) } catch { return false }
      }),
    }))
    .filter((section) => section.items.length > 0)
}

export function getQuickActions(role) {
  return getAccessibleNavigation(role)
    .flatMap((section) => section.items)
    .filter((item) => item.to !== '/')
}
