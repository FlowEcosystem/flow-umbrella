<script setup>
const props = defineProps({
  to: { type: String, required: true },
  label: { type: String, required: true },
  icon: { type: String, required: true },
  tooltip: { type: String, default: '' },
  collapsed: { type: Boolean, default: false },
  exact: { type: Boolean, default: false },
})

const route = useRoute()

const isActive = computed(() => {
  if (props.exact) return route.path === props.to
  return route.path === props.to || route.path.startsWith(`${props.to}/`)
})
</script>

<template>
  <RouterLink :to="to" custom v-slot="{ href, navigate }">
    <a
      :href="href"
      v-tooltip.right="props.collapsed ? tooltip : null"
      class="sidebar-link"
      :class="{
        'sidebar-link--active': isActive,
        'sidebar-link--collapsed': props.collapsed,
      }"
      :aria-label="props.collapsed ? label : undefined"
      :aria-current="isActive ? 'page' : undefined"
      @click="navigate"
    >
      <component :is="icon" class="icon-md" />
      <span v-if="!props.collapsed" class="sidebar-link-label">{{ label }}</span>
      <span v-else class="sr-only">{{ label }}</span>
    </a>
  </RouterLink>
</template>
