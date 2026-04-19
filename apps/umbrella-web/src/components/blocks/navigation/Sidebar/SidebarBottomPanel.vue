<script setup>
import router from '@/plugins/router'

const authStore = useAuthStore()
const logoutModal = ref(null)

function openLogout() {
  logoutModal.value?.open()
}

async function doLogout() {
  await authStore.logout()
  router.push('/')
}
</script>

<template>
  <div class="flex flex-col items-center gap-1">
    <UiRouteButton to="/settings" tooltip="Настройки">
      <Settings class="size-5" />
    </UiRouteButton>

    <div class="tooltip tooltip-right" data-tip="Выйти">
      <button
        class="btn btn-ghost btn-square rounded-2xl"
        :disabled="!authStore.isAuthenticated"
        @click="openLogout"
      >
        <SquareArrowRightExit class="size-5" />
      </button>
    </div>

    <UiConfirmModal
      ref="logoutModal"
      title="Выйти из системы?"
      icon="SquareArrowRightExit"
      message="Сессия будет завершена. Чтобы продолжить работу, потребуется войти снова."
      confirm-text="Выйти"
      cancel-text="Отмена"
      confirm-variant="error"
      busy-text="Выходим…"
      @confirm="doLogout"
    />
  </div>
</template>
