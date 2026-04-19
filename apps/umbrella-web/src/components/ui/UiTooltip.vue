<template>
  <div class="tooltip" :class="positionClass" :data-tip="text">
    <slot />
  </div>
</template>

<script setup>
const props = defineProps({
  text: String,
  position: {
    type: String,
    default: "bottom",
  },
});

const positionClass = `tooltip-${props.position}`;
</script>
