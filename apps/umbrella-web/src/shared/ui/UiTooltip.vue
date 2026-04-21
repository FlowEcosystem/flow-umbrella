<script setup>
defineProps({
  text: { type: String, default: '' },
  position: { type: String, default: 'bottom' },
})
</script>

<template>
  <span v-tooltip="{ value: text, position }">
    <slot />
  </span>
</template>
