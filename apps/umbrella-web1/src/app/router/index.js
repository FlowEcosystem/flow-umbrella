import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/domains/auth/store'

import DefaultLayout from '@/app/layouts/DefaultLayout.vue'
import LoginPage     from '@/domains/auth/ui/pages/LoginPage.vue'
import DashboardPage from '@/domains/dashboard/ui/pages/DashboardPage.vue'
import AgentsPage       from '@/domains/agents/ui/pages/AgentsPage.vue'
import AgentDetailPage  from '@/domains/agents/ui/pages/AgentDetailPage.vue'
import PoliciesPage  from '@/domains/policies/ui/pages/PoliciesPage.vue'
import GroupsPage       from '@/domains/groups/ui/pages/GroupsPage.vue'
import GroupDetailPage  from '@/domains/groups/ui/pages/GroupDetailPage.vue'
import AdminsPage    from '@/domains/admins/ui/pages/AdminsPage.vue'
import SettingsPage  from '@/domains/settings/ui/pages/SettingsPage.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginPage, meta: { public: true } },
    {
      path: '/',
      component: DefaultLayout,
      children: [
        { path: '',         component: DashboardPage },
        { path: 'agents',        component: AgentsPage },
        { path: 'agents/:id',   component: AgentDetailPage },
        { path: 'policies', component: PoliciesPage },
        { path: 'groups',        component: GroupsPage },
        { path: 'groups/:id',   component: GroupDetailPage },
        { path: 'admins',   component: AdminsPage, meta: { superAdminOnly: true } },
        { path: 'settings', component: SettingsPage },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.ensureInitialized()

  if (!to.meta.public && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    return { path: '/' }
  }
  if (to.meta.superAdminOnly && auth.currentUser?.role !== 'superadmin') {
    return { path: '/' }
  }
})
