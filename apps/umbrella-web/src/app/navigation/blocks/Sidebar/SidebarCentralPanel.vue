<script setup>
import { useNavigation } from '@/app/navigation/composables/useNavigation'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
})

const { sections } = useNavigation()
</script>

<template>
  <div class="sidebar-central-panel">
    <nav class="sidebar-nav">
      <section
        v-for="section in sections"
        :key="section.key"
        class="sidebar-section"
        :class="{ 'sidebar-section--bottom': section.bottom }"
      >
        <div v-if="!props.collapsed && section.label" class="sidebar-section-label">{{ section.label }}</div>

        <div class="sidebar-section-panel" :class="{ 'sidebar-section-panel--collapsed': props.collapsed }">
          <SidebarNavLink
            v-for="item in section.items"
            :key="item.to"
            :to="item.to"
            :label="item.label"
            :icon="item.icon"
            :tooltip="item.tooltip"
            :collapsed="props.collapsed"
            :exact="item.exact"
          />
        </div>
      </section>
    </nav>
  </div>
</template>
