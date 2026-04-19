<script setup>
import { useAuthStore } from '@/stores/auth.store'
import { useBreadcrumbs } from '@/composables/navigation/useBreadcrumbs'
import { getRoleLabel } from '@/config/rbac'

const authStore = useAuthStore()
const { crumbs } = useBreadcrumbs()

defineProps({
  mobile: { type: Boolean, default: false },
})

defineEmits(['toggle-sidebar'])
</script>

<template>
  <header class="app-navbar">
    <div class="navbar-left">
      <button
        v-if="mobile"
        type="button"
        class="navbar-sidebar-toggle"
        aria-label="Открыть боковое меню"
        @click="$emit('toggle-sidebar')"
      >
        <PanelLeft class="icon-sm" />
      </button>

      <NavbarBreadcrumbs :items="crumbs" />
    </div>

    <div class="navbar-right">
      <NavbarUserInfo
        :user-full-name="
          authStore.currentUser?.full_name ?? authStore.currentUser?.email ?? 'Пользователь'
        "
        :user-position="getRoleLabel(authStore.currentUser?.role)"
      />
    </div>
  </header>
</template>
