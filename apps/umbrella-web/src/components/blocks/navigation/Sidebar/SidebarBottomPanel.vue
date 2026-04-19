<script setup>
const props = defineProps({
  collapsed: { type: Boolean, default: false },
})

const appVersion = import.meta.env.VITE_APP_VERSION ?? '1.0.0'
</script>

<template>
  <div class="sidebar-bottom-panel">
    <div
      v-if="props.collapsed"
      class="sidebar-bottom-icon"
      v-tooltip.right="`Консоль Umbrella v${appVersion}`"
      aria-hidden="true"
    >
      <Shield class="icon-md" />
    </div>

    <div v-else class="sidebar-version">
      <span class="sidebar-version-label">Рабочая среда</span>
      <span class="sidebar-version-title">Консоль Umbrella</span>
      <span class="sidebar-version-value">v{{ appVersion }}</span>
    </div>
  </div>
</template>
