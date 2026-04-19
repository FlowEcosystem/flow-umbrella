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
        roles: [],
      },
    ],
  },
])

export function getAccessibleNavigation(role) {
  return navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => !item.roles.length || item.roles.includes(role)),
    }))
    .filter((section) => section.items.length > 0)
}

export function getQuickActions(role) {
  return getAccessibleNavigation(role)
    .flatMap((section) => section.items)
    .filter((item) => item.to !== '/')
}
