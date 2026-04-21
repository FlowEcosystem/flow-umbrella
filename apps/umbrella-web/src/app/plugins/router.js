import { ref } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import pinia from '@/app/plugins/pinia'
import { useAuthStore } from '@/domains/auth/store'
import { roleHasCapability } from '@/app/access/capabilities'

const DefaultLayout = () => import('@/app/layouts/DefaultLayout.vue')
const EmptyLayout = () => import('@/app/layouts/EmptyLayout.vue')

const HomePage = () => import('@/app/pages/general/HomePage.vue')
const NotFoundPage = () => import('@/app/pages/general/NotFoundPage.vue')
const ForbiddenPage = () => import('@/app/pages/general/ForbiddenPage.vue')
const LoginPage = () => import('@/domains/auth/ui/pages/LoginPage.vue')
const SettingsPage = () => import('@/domains/auth/ui/pages/SettingsPage.vue')
const AdminsPage = () => import('@/domains/admins/ui/pages/AdminsPage.vue')
const AgentsPage = () => import('@/domains/agents/ui/pages/AgentsPage.vue')
const GroupsPage = () => import('@/domains/groups/ui/pages/GroupsPage.vue')
export const isRouteNavigating = ref(true)

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
          crumb: 'Обзор',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: SettingsPage,
        meta: {
          crumb: 'Настройки',
          capability: 'self:read',
        },
      },
      {
        path: 'admins',
        name: 'admins',
        component: AdminsPage,
        meta: {
          crumb: 'Администраторы',
          capability: 'admins:read',
        },
      },
      {
        path: 'agents',
        name: 'agents',
        component: AgentsPage,
        meta: {
          crumb: 'Агенты',
          capability: 'agents:read',
        },
      },
      {
        path: 'groups',
        name: 'groups',
        component: GroupsPage,
        meta: {
          crumb: 'Группы',
          capability: 'groups:read',
        },
      },
    ],
  },
  {
    path: '/login',
    component: EmptyLayout,
    children: [
      {
        path: '',
        name: 'login',
        component: LoginPage,
        meta: { public: true },
      },
    ],
  },
  {
    path: '/403',
    component: EmptyLayout,
    children: [
      {
        path: '',
        name: 'forbidden',
        component: ForbiddenPage,
        meta: { public: true },
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
        meta: { public: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  isRouteNavigating.value = true
  const authStore = useAuthStore(pinia)
  await authStore.ensureInitialized()

  const isPublic = to.matched.some((record) => record.meta?.public)

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { path: '/' }
  }

  if (isPublic) return true

  if (!authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  const capability = to.matched.findLast((r) => r.meta?.capability)?.meta?.capability
  if (capability && !roleHasCapability(authStore.currentUser?.role, capability)) {
    return {
      name: 'forbidden',
      query: { from: to.fullPath },
    }
  }

  return true
})

router.afterEach(() => {
  isRouteNavigating.value = false
})

router.onError(() => {
  isRouteNavigating.value = false
})

export default router
