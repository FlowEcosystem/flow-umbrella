<script setup>
import Button from 'primevue/button'
import { Plus } from 'lucide-vue-next'

defineProps({
  canWriteGroups: {
    type: Boolean,
    default: false,
  },
  onOpenCreate: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <header class="page-header">
    <div class="page-header__copy">
      <h1 class="page-title">Группы</h1>
      <p class="page-subtitle">Организация агентов по группам и управление составом.</p>
    </div>
    <Button v-if="canWriteGroups" @click="onOpenCreate">
      <Plus :size="16" />
      <span>Создать группу</span>
    </Button>
  </header>
</template>
