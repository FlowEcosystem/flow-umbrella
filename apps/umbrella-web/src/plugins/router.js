import { createRouter, createWebHistory } from 'vue-router'

import pinia from '@/plugins/pinia'
import { ROLES } from '@/config/rbac'
import { useAuthStore } from '@/stores/auth.store'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import EmptyLayout from '@/layouts/EmptyLayout.vue'

import HomePage from '@/pages/general/HomePage.vue'
import NotFoundPage from '@/pages/general/NotFoundPage.vue'
import ForbiddenPage from '@/pages/general/ForbiddenPage.vue'
import SettingsPage from '@/pages/general/SettingsPage.vue'

import SheetPage from '@/pages/sheets/SheetPage.vue'
import StudentPage from '@/pages/students/StudentPage.vue'
import GroupPage from '@/pages/students/GroupPage.vue'
import SchedulePage from '@/pages/schedule/SchedulePage.vue'
import DisciplinePage from '@/pages/discipline/DisciplinePage.vue'
import HomeworkPage from '@/pages/homework/HomeworkPage.vue'
import MaterialsPage from '@/pages/materials/MaterialsPage.vue'
import ReportsPage from '@/pages/reports/ReportsPage.vue'
import AdministrationPage from '@/pages/admin/AdministrationPage.vue'

const academicRoles = [ROLES.STUDENT, ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR]
const staffRoles = [ROLES.TEACHER, ROLES.MANAGER, ROLES.DIRECTOR]
const managementRoles = [ROLES.MANAGER, ROLES.DIRECTOR]

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: HomePage,
        meta: {
          public: true,
          crumb: 'Главная',
          icon: 'House',
        },
      },
      {
        path: 'schedule',
        name: 'schedule',
        component: SchedulePage,
        meta: {
          roles: academicRoles,
          crumb: 'Расписание',
          icon: 'CalendarDays',
        },
      },
      {
        path: 'homework',
        name: 'homework',
        component: HomeworkPage,
        meta: {
          roles: academicRoles,
          crumb: 'Домашние задания',
          icon: 'NotebookPen',
        },
      },
      {
        path: 'grades',
        name: 'grades',
        component: SheetPage,
        meta: {
          roles: academicRoles,
          crumb: 'Оценки',
          icon: 'ClipboardCheck',
        },
      },
      {
        path: 'materials',
        name: 'materials',
        component: MaterialsPage,
        meta: {
          roles: academicRoles,
          crumb: 'Методпакеты',
          icon: 'LibraryBig',
        },
      },
      {
        path: 'students',
        name: 'students',
        component: StudentPage,
        meta: {
          roles: staffRoles,
          crumb: 'Студенты',
          icon: 'GraduationCap',
        },
      },
      {
        path: 'groups',
        name: 'groups',
        component: GroupPage,
        meta: {
          roles: staffRoles,
          crumb: 'Группы',
          icon: 'Users',
        },
      },
      {
        path: 'disciplines',
        name: 'disciplines',
        component: DisciplinePage,
        meta: {
          roles: managementRoles,
          crumb: 'Дисциплины',
          icon: 'BookOpenText',
        },
      },
      {
        path: 'reports',
        name: 'reports',
        component: ReportsPage,
        meta: {
          roles: managementRoles,
          crumb: 'Отчеты',
          icon: 'ChartColumnBig',
        },
      },
      {
        path: 'administration',
        name: 'administration',
        component: AdministrationPage,
        meta: {
          roles: managementRoles,
          crumb: 'Администрирование',
          icon: 'ShieldCheck',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: SettingsPage,
        meta: {
          public: true,
          crumb: 'Настройки',
          icon: 'Settings',
        },
      },
    ],
  },
  {
    path: '/forbidden',
    component: EmptyLayout,
    children: [
      {
        path: '',
        name: 'forbidden',
        component: ForbiddenPage,
        meta: {
          public: true,
          crumb: 'Нет доступа',
          icon: 'ShieldAlert',
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    component: EmptyLayout,
    children: [
      {
        path: '',
        name: 'not-found',
        component: NotFoundPage,
        meta: {
          public: true,
          title: 'notFoundPage',
        },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia)
  await authStore.ensureInitialized()

  const publicRoute = to.matched.some((record) => record.meta?.public)

  if (publicRoute) {
    return true
  }

  if (!authStore.isAuthenticated) {
    return {
      name: 'home',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  const requiredRoles = to.matched.flatMap((record) => record.meta?.roles ?? [])

  if (requiredRoles.length && !authStore.hasRole(requiredRoles)) {
    return {
      name: 'forbidden',
      query: {
        from: to.fullPath,
      },
    }
  }

  return true
})

export default router
