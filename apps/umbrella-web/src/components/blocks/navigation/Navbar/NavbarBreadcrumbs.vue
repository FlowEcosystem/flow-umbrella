<script setup>
const props = defineProps({
  items: { type: Array, required: true },
})

const lastIndex = computed(() => Math.max(props.items.length - 1, 0))
</script>

<template>
  <div class="breadcrumbs text-sm p-0">
    <ul class="text-base-content/70">
      <li v-for="(c, i) in props.items" :key="i" :class="i < lastIndex ? 'hidden sm:flex' : ''">
        <router-link :to="c.to" class="flex items-center gap-2 hover:text-base-content transition">
          <component :is="c.icon" class="size-4" />
          <span class="hidden md:inline">{{ c.label }}</span>
        </router-link>
      </li>
    </ul>
  </div>
</template>
