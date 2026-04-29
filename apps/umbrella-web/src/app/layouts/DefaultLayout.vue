<script setup>
import {
  LayoutDashboard, Monitor, ShieldCheck,
  Users, UserCircle, Settings, ClipboardList,
  PackageOpen, ChevronsUpDown, LogOut,
} from 'lucide-vue-next'
import { useAuthStore }       from '@/domains/auth/store'
import { useSessionExpired }  from '@/shared/composables/useSessionExpired'
import { usePermissions }     from '@/shared/composables/usePermissions'
import { useGlobalStream }    from '@/shared/composables/useGlobalStream'

const route    = useRoute()
const router   = useRouter()
const auth     = useAuthStore()

const { sessionExpired, reset: resetSession } = useSessionExpired()
const { isSuperAdmin } = usePermissions()

useGlobalStream()

async function handleSessionExpiredLogin() {
  resetSession()
  await auth.logout()
  router.push('/login')
}

const userInitials = computed(() => {
  const name = auth.currentUser?.full_name ?? auth.currentUser?.email ?? ''
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'
})

const userName = computed(() => auth.currentUser?.full_name ?? auth.currentUser?.email ?? '')

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

const allNavItems = [
  { icon: LayoutDashboard, label: 'Обзор',     path: '/' },
  { icon: Monitor,         label: 'Агенты',    path: '/agents' },
  { icon: ShieldCheck,     label: 'Политики',  path: '/policies' },
  { icon: Users,           label: 'Группы',    path: '/groups' },
  { icon: ClipboardList,   label: 'Аудит',     path: '/audit' },
  { icon: PackageOpen,     label: 'Релизы',    path: '/releases' },
  { icon: UserCircle,      label: 'Админы',    path: '/admins', superAdminOnly: true },
  { icon: Settings,        label: 'Настройки', path: '/settings' },
]

const navItems = computed(() =>
  allNavItems.filter(item => !item.superAdminOnly || isSuperAdmin.value)
)

const pageTitle = computed(() => {
  const p = route.path
  if (p === '/')         return 'Обзор'
  if (p === '/agents')          return 'Агенты'
  if (p.startsWith('/agents/')) return 'Агент'
  if (p === '/audit')           return 'Аудит'
  if (p === '/policies')        return 'Политики'
  if (p === '/groups')          return 'Группы'
  if (p.startsWith('/groups/')) return 'Группа'
  if (p === '/admins')    return 'Администраторы'
  if (p === '/releases')  return 'Релизы'
  if (p === '/settings')  return 'Настройки'
  return 'Umbrella'
})
</script>

<template>
  <TooltipProvider :delay-duration="400">
  <div class="flex h-screen bg-bg overflow-hidden">

    <!-- sidebar -->
    <aside class="w-[52px] flex flex-col items-center py-4 border-r border-white/[0.06] bg-bg-sidebar flex-shrink-0">

      <!-- logo -->
      <div class="w-8 h-8 rounded-lg flex items-center justify-center mb-6 flex-shrink-0"
           style="background: linear-gradient(135deg, #b5603e 0%, #d4785a 100%)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 1.5C4.41 1.5 1.5 4.41 1.5 8c0 1.8.72 3.43 1.88 4.62L8 8l4.62 4.62A6.48 6.48 0 0 0 14.5 8c0-3.59-2.91-6.5-6.5-6.5Z" fill="white" fill-opacity=".9"/>
          <path d="M8 8 3.38 12.62A6.48 6.48 0 0 0 8 14.5c1.8 0 3.43-.72 4.62-1.88L8 8Z" fill="white" fill-opacity=".5"/>
        </svg>
      </div>

      <!-- nav -->
      <nav class="flex flex-col items-center gap-1 flex-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="w-9 h-9 rounded-lg flex items-center justify-center transition-colors group relative"
          :class="(item.path === '/' ? route.path === '/' : route.path.startsWith(item.path))
            ? 'bg-white/[0.08] text-fg'
            : 'text-fg-subtle hover:text-fg-muted hover:bg-white/[0.04]'"
        >
          <component :is="item.icon" :size="18" :stroke-width="1.5" />
          <!-- tooltip -->
          <span class="absolute left-full ml-2.5 px-2 py-1 rounded-md text-xs bg-bg-overlay text-fg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 border border-white/[0.08]">
            {{ item.label }}
          </span>
        </RouterLink>
      </nav>

      <!-- bottom user avatar -->
      <div class="flex flex-col items-center gap-1 mt-auto">
        <div class="w-9 h-9 rounded-full overflow-hidden shrink-0">
          <img v-if="auth.currentUser?.avatar_url"
               :src="auth.currentUser.avatar_url"
               :alt="userInitials"
               class="w-full h-full object-cover" />
          <div v-else class="w-full h-full bg-accent-dim flex items-center justify-center">
            <span class="text-accent text-[10px] font-medium">{{ userInitials }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- main area -->
    <div class="flex flex-col flex-1 min-w-0">

      <!-- topbar -->
      <header class="h-11 flex items-center justify-between px-5 border-b border-white/[0.06] flex-shrink-0">
        <span class="text-sm text-fg-muted">{{ pageTitle }}</span>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-2 px-2.5 py-1.5 rounded-md hover:bg-white/[0.04] cursor-pointer transition-colors">
            <div class="w-8 h-8 rounded-full overflow-hidden shrink-0">
              <img v-if="auth.currentUser?.avatar_url"
                   :src="auth.currentUser.avatar_url"
                   :alt="userInitials"
                   class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-accent-dim flex items-center justify-center">
                <span class="text-accent text-xs font-medium">{{ userInitials }}</span>
              </div>
            </div>
            <span class="text-sm text-fg">{{ userName }}</span>
            <ChevronsUpDown :size="14" class="text-fg-subtle" />
          </div>
          <button
            @click="handleLogout"
            class="p-1.5 rounded-md text-fg-subtle hover:text-fg hover:bg-white/[0.04] transition-colors"
            title="Выйти"
          >
            <LogOut :size="14" />
          </button>
        </div>
      </header>

      <!-- page content -->
      <main class="flex-1 overflow-y-auto">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>

      <!-- statusbar -->
      <footer class="h-8 flex items-center justify-between px-5 border-t border-white/[0.06] flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1.5">
            <div class="w-4 h-4 rounded flex items-center justify-center"
                 style="background: linear-gradient(135deg, #b5603e 0%, #d4785a 100%)">
              <svg width="8" height="8" viewBox="0 0 16 16" fill="none">
                <path d="M8 1.5C4.41 1.5 1.5 4.41 1.5 8c0 1.8.72 3.43 1.88 4.62L8 8l4.62 4.62A6.48 6.48 0 0 0 14.5 8c0-3.59-2.91-6.5-6.5-6.5Z" fill="white" fill-opacity=".9"/>
              </svg>
            </div>
            <span class="text-xs text-fg-muted">Umbrella</span>
          </div>
          <span class="text-fg-subtle text-xs">|</span>
          <span class="text-xs text-fg-subtle">Консоль управления</span>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="auth.currentUser?.role"
                class="text-xs text-fg-subtle/50 capitalize">
            {{ auth.currentUser.role }}
          </span>
          <span class="text-fg-subtle text-xs">·</span>
          <span class="text-xs text-fg-subtle">v1.0.0</span>
          <span class="text-fg-subtle text-xs">·</span>
          <div class="flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span class="text-xs text-fg-subtle">Активна</span>
          </div>
        </div>
      </footer>

    </div>
  </div>
  </TooltipProvider>

  <UiToastContainer />

  <UiConfirmDialog
    :open="sessionExpired"
    variant="warning"
    title="Сессия истекла"
    description="Токен авторизации недействителен или был отозван. Войдите в аккаунт заново, чтобы продолжить работу."
    confirm-text="Войти заново"
    cancel-text="Отмена"
    @update:open="v => !v && resetSession()"
    @confirm="handleSessionExpiredLogin"
  />
</template>
