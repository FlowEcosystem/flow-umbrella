<script setup>
import { getRoleLabel } from '@/config/rbac'
import { useBreadcrumbs } from '@/composables/navigation/useBreadcrumbs'
import { useNotificationsStore } from '@/stores/notifications.store'
import { useAuthStore } from '@/stores/auth.store'

const authStore = useAuthStore()
const notsStore = useNotificationsStore()
const { crumbs } = useBreadcrumbs()

const panelTitle = computed(() =>
  authStore.isAuthenticated ? `Кабинет: ${getRoleLabel(authStore.role)}` : 'Публичный контур',
)
const userRoleSubtitle = computed(() =>
  authStore.isAuthenticated ? getRoleLabel(authStore.role) : 'Нет активной сессии',
)

watch(
  () => authStore.isAuthenticated,
  (isAuthenticated) => {
    if (isAuthenticated) {
      notsStore.fetchLatest()
      return
    }

    notsStore.reset()
  },
  { immediate: true },
)
</script>

<template>
  <header class="h-14 px-4 border-b border-base-200 bg-base-100 flex items-center gap-4 shadow-sm">
    <div
      class="flex items-center gap-3 text-sm rounded-2xl px-3 py-2 bg-base-100/60 backdrop-blur border border-base-200 shadow-sm"
    >
      <span class="font-semibold">{{ panelTitle }}</span>

      <div class="divider divider-horizontal mx-0 opacity-60"></div>

      <NavbarBreadcrumbs :items="crumbs" />
    </div>

    <div class="flex-1"></div>

    <div class="flex items-center gap-2">
      <NavbarNotification
        :nots="notsStore.notifications"
        :unreadCount="notsStore.unreadCount"
        :actions="{
          read: notsStore.markRead,
          readAll: notsStore.markAllRead,
          clear: notsStore.clear,
        }"
      />

      <NavbarUserInfo
        :user-full-name="authStore.displayName"
        :user-position="userRoleSubtitle"
        :user-avatar-url="authStore.user?.avatarUrl"
      />
    </div>
  </header>
</template>
