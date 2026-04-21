<script setup>
import Button from 'primevue/button'
import { Plus } from 'lucide-vue-next'

defineProps({
  canWriteAgents: {
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
      <h1 class="page-title">Агенты</h1>
      <p class="page-subtitle">Управление машинами, их состоянием и enrollment-токенами.</p>
    </div>
    <Button v-if="canWriteAgents" @click="onOpenCreate">
      <Plus :size="16" />
      <span>Добавить агента</span>
    </Button>
  </header>
</template>
