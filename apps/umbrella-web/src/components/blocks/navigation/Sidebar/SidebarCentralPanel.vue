<script setup>
import { useNavigation } from '@/composables/navigation/useNavigation'

const { sections } = useNavigation()
</script>

<template>
  <nav class="flex flex-col items-center gap-1">
    <template v-for="(section, index) in sections" :key="section.key">
      <UiRouteButton
        v-for="item in section.items"
        :key="item.to"
        :to="item.to"
        :tooltip="item.tooltip"
        :exact="item.exact"
      >
        <component :is="item.icon" class="size-5" />
      </UiRouteButton>

      <div v-if="index < sections.length - 1" class="divider my-0"></div>
    </template>
  </nav>
</template>
