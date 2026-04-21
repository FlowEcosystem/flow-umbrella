<script setup>
import { useAuthStore } from '@/domains/auth/store'

const props = defineProps({
  userFullName: { type: String, default: 'Пользователь' },
  userPosition: { type: String, default: '' },
})

const authStore = useAuthStore()
const router = useRouter()
const menu = ref()
const avatarError = ref(false)

const avatarUrl = computed(() => authStore.currentUser?.avatar_url || '')

watch(avatarUrl, () => {
  avatarError.value = false
})

function handleAvatarError() {
  avatarError.value = true
}

const menuItems = computed(() => [
  {
    label: 'Настройки',
    icon: 'Settings',
    command: goToSettings,
  },
  {
    separator: true,
  },
  {
    label: 'Выйти',
    icon: 'LogOut',
    command: handleLogout,
    danger: true,
  },
])

const initials = computed(() =>
  props.userFullName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase(),
)

function toggleMenu(event) {
  menu.value?.toggle(event)
}

function goToSettings() {
  menu.value?.hide?.()
  router.push('/settings')
}

async function handleLogout() {
  menu.value?.hide?.()
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="navbar-user">
    <button
      type="button"
      class="navbar-user-trigger"
      :disabled="!authStore.isAuthenticated"
      @click="toggleMenu"
    >
      <span class="navbar-avatar">
        <img
          v-if="avatarUrl && !avatarError"
          :src="avatarUrl"
          :alt="userFullName"
          class="navbar-avatar-img"
          @error="handleAvatarError"
        />
        <span v-else class="navbar-avatar-fallback">
          {{ initials || 'Сотрудник' }}
        </span>
      </span>

      <span class="navbar-user-name">{{ userFullName }}</span>
      <ChevronDown class="icon-sm navbar-user-chevron" />
    </button>

    <Menu ref="menu" :model="menuItems" popup>
      <template #start>
        <div class="menu-user-summary">
          <span class="menu-user-title">{{ userFullName }}</span>
          <span v-if="userPosition" class="menu-user-subtitle">{{ userPosition }}</span>
        </div>
      </template>

      <template #item="{ item, props: itemProps }">
        <a
          v-bind="itemProps.action"
          class="menu-item"
          :class="{ 'menu-item--danger': item.danger }"
        >
          <component :is="item.icon" class="icon-sm" />
          <span>{{ item.label }}</span>
        </a>
      </template>
    </Menu>
  </div>
</template>
