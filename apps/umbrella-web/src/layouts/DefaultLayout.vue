<script setup>
const SIDEBAR_STATE_KEY = 'umbrella-sidebar-collapsed'

const route = useRoute()

const isMobile = ref(false)
const isSidebarOpen = ref(false)
const isSidebarCollapsed = ref(false)

function readSidebarPreference() {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(SIDEBAR_STATE_KEY) === 'true'
}

function writeSidebarPreference(value) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SIDEBAR_STATE_KEY, String(value))
}

function syncLayout() {
  const mobile = window.innerWidth < 1024
  isMobile.value = mobile
  isSidebarOpen.value = mobile ? false : true
}

function toggleSidebar() {
  if (isMobile.value) {
    isSidebarOpen.value = !isSidebarOpen.value
    return
  }

  isSidebarCollapsed.value = !isSidebarCollapsed.value
  writeSidebarPreference(isSidebarCollapsed.value)
}

function closeSidebar() {
  if (isMobile.value) isSidebarOpen.value = false
}

onMounted(() => {
  isSidebarCollapsed.value = readSidebarPreference()
  syncLayout()
  window.addEventListener('resize', syncLayout)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncLayout)
})

watch(
  () => route.fullPath,
  () => {
    closeSidebar()
  },
)
</script>

<template>
  <div class="app-layout">
    <AppSidebar
      :collapsed="!isMobile && isSidebarCollapsed"
      :mobile="isMobile"
      :open="isSidebarOpen"
      @toggle="toggleSidebar"
    />
    <button
      v-if="isMobile && isSidebarOpen"
      type="button"
      class="app-overlay"
      aria-label="Закрыть боковое меню"
      @click="closeSidebar"
    />
    <div class="app-main">
      <AppNavbar :mobile="isMobile" @toggle-sidebar="toggleSidebar" />
      <main class="app-content">
        <div class="app-page-shell">
          <router-view />
        </div>
      </main>
      <AppFooter />
    </div>
  </div>
</template>
