<script setup>
import Button from 'primevue/button'
import { Plus } from 'lucide-vue-next'

defineProps({
  canManageAdmins: {
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
  <header class="admins-page__header">
    <h1 class="admins-page__title">Администраторы</h1>
    <Button v-if="canManageAdmins" @click="onOpenCreate">
      <Plus :size="16" />
      <span>Добавить администратора</span>
    </Button>
  </header>
</template>
