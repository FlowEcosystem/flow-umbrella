<script setup>
const props = defineProps({
  collapsed: { type: Boolean, default: false },
  mobile: { type: Boolean, default: false },
})

defineEmits(['toggle'])
</script>

<template>
  <div class="sidebar-top-panel" :class="{ 'sidebar-top-panel--collapsed': props.collapsed && !props.mobile }">
    <button
      v-if="props.collapsed && !props.mobile"
      type="button"
      class="sidebar-brand-toggle"
      aria-label="Развернуть меню"
      @click="$emit('toggle')"
    >
      <Shield class="icon-md" />
    </button>

    <RouterLink v-else to="/" class="sidebar-brand" :aria-label="'Umbrella'">
      <span class="sidebar-brand-mark">
        <Shield class="icon-md" />
      </span>
      <span class="sidebar-brand-name">Umbrella</span>
    </RouterLink>

    <button
      v-if="!props.collapsed || props.mobile"
      type="button"
      class="sidebar-brand-toggle"
      :aria-label="props.mobile ? 'Закрыть меню' : 'Свернуть меню'"
      @click="$emit('toggle')"
    >
      <X v-if="props.mobile" class="icon-sm" />
      <PanelLeftClose v-else class="icon-sm" />
    </button>
  </div>
</template>
