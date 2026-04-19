import { ROLES } from '@/config/rbac'

export const navigationSections = Object.freeze([
  {
    key: 'general',
    items: [
      {
        to: '/',
        label: 'Главная',
        tooltip: 'Главная',
        icon: 'House',
        exact: true,
        roles: [],
      },
      {
        to: '/schedule',
        label: 'Расписание',
        tooltip: 'Расписание',
        icon: 'CalendarDays',
        roles: [ROLES.STUDENT, ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR],
      },
    ],
  },
  {
    key: 'learning',
    items: [
      {
        to: '/homework',
        label: 'Домашние задания',
        tooltip: 'Домашние задания',
        icon: 'NotebookPen',
        roles: [ROLES.STUDENT, ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR],
      },
      {
        to: '/grades',
        label: 'Оценки',
        tooltip: 'Оценки и ведомости',
        icon: 'ClipboardCheck',
        roles: [ROLES.STUDENT, ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR],
      },
      {
        to: '/materials',
        label: 'Методпакеты',
        tooltip: 'Методические материалы',
        icon: 'LibraryBig',
        roles: [ROLES.STUDENT, ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR],
      },
    ],
  },
  {
    key: 'teaching',
    items: [
      {
        to: '/groups',
        label: 'Группы',
        tooltip: 'Группы',
        icon: 'Users',
        roles: [ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR],
      },
      {
        to: '/students',
        label: 'Студенты',
        tooltip: 'Студенты',
        icon: 'GraduationCap',
        roles: [ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR],
      },
      {
        to: '/disciplines',
        label: 'Дисциплины',
        tooltip: 'Дисциплины',
        icon: 'BookOpenText',
        roles: [ROLES.MANAGER, ROLES.DIRECTOR],
      },
    ],
  },
  {
    key: 'management',
    items: [
      {
        to: '/reports',
        label: 'Отчеты',
        tooltip: 'Отчеты и статистика',
        icon: 'ChartColumnBig',
        roles: [ROLES.MANAGER, ROLES.DIRECTOR],
      },
      {
        to: '/administration',
        label: 'Администрирование',
        tooltip: 'Администрирование',
        icon: 'ShieldCheck',
        roles: [ROLES.MANAGER, ROLES.DIRECTOR],
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
