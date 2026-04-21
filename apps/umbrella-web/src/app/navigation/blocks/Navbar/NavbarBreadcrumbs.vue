<script setup>
const props = defineProps({
  items: { type: Array, required: true },
})
</script>

<template>
  <nav class="breadcrumbs">
    <ol>
      <li v-for="(c, i) in props.items" :key="i">
        <router-link v-if="i < props.items.length - 1" :to="c.to" class="breadcrumb-link">
          <span>{{ c.label }}</span>
        </router-link>
        <span v-else class="breadcrumb-current">{{ c.label }}</span>
        <ChevronRight v-if="i < props.items.length - 1" class="icon-sm breadcrumb-sep" />
      </li>
    </ol>
  </nav>
</template>
