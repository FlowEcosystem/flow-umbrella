<script setup>
import { isRouteNavigating } from '@/plugins/router'
import { useAuthStore } from '@/stores/auth.store'

const authStore = useAuthStore()
const route = useRoute()

const isPublicRoute = computed(() => route.matched.some((record) => record.meta?.public))

const showAppLoader = computed(() => {
  if (isRouteNavigating.value) return true
  return !authStore.ready && !isPublicRoute.value
})
</script>

<template>
  <div class="app-root">
    <Toast position="top-right" />
    <router-view />

    <Transition name="app-loader-fade">
      <AppBootLoader v-if="showAppLoader" />
    </Transition>
  </div>
</template>
