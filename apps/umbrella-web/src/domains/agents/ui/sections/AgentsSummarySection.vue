<script setup>
defineProps({
  items: {
    type: Array,
    required: true,
  },
  variant: {
    type: String,
    default: 'top',
  },
  isChipActive: {
    type: Function,
    required: true,
  },
  onChipClick: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <section class="agents-summary" :class="variant === 'sidebar' ? 'agents-summary--sidebar' : 'agents-summary--top'">
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      class="agents-summary__item"
      :class="[`agents-summary__item--${item.key}`, { 'is-active': isChipActive(item.key) }]"
      @click="onChipClick(item.key)"
    >
      <span class="agents-summary__label">{{ item.label }}</span>
      <strong class="agents-summary__value">{{ item.count }}</strong>
    </button>
  </section>
</template>
