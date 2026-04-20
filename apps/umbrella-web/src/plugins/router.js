import { ref } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import pinia from '@/plugins/pinia'
import { useAuthStore } from '@/stores/auth.store'
import { roleHasCapability } from '@/config/capabilities'

const DefaultLayout = () => import('@/layouts/DefaultLayout.vue')
const EmptyLayout = () => import('@/layouts/EmptyLayout.vue')

const HomePage = () => import('@/pages/general/HomePage.vue')
const NotFoundPage = () => import('@/pages/general/NotFoundPage.vue')
const ForbiddenPage = () => import('@/pages/general/ForbiddenPage.vue')
const LoginPage = () => import('@/pages/auth/LoginPage.vue')
const SettingsPage = () => import('@/pages/settings/SettingsPage.vue')
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
