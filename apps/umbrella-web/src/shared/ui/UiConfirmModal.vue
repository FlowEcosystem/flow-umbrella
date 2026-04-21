<script setup>
const props = defineProps({
  title: { type: String, default: 'Подтверждение действия' },
  icon: { type: String },
  message: { type: String, default: '' },
  confirmText: { type: String, default: 'Подтвердить' },
  cancelText: { type: String, default: 'Отмена' },
  confirmVariant: { type: String, default: 'primary' },
  busyText: { type: String, default: 'Выполняется...' },
  action: { type: Function, default: null },
})

const emit = defineEmits(['confirm', 'cancel', 'open', 'close'])

const visible = ref(false)
const busy = ref(false)

const confirmSeverity = computed(() => {
  const map = { error: 'danger', primary: 'primary', warning: 'warning', success: 'success', neutral: 'secondary' }
  return map[props.confirmVariant] ?? 'primary'
})

function open() {
  visible.value = true
  emit('open')
}

function close() {
  visible.value = false
  emit('close')
}

function onCancel() {
  if (busy.value) return
  emit('cancel')
  close()
}

async function onConfirm() {
  if (busy.value) return
  busy.value = true
  try {
    if (props.action) await props.action()
    emit('confirm')
    close()
  } finally {
    busy.value = false
  }
}

defineExpose({ open, close, busy })
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="title"
    :closable="!busy"
    :style="{ width: '420px', maxWidth: 'calc(100vw - 32px)' }"
  >
    <p v-if="message" class="modal-message">{{ message }}</p>
    <slot />

    <template #footer>
      <Button :label="cancelText" outlined severity="secondary" :disabled="busy" @click="onCancel" />
      <Button
        :label="busy ? busyText : confirmText"
        :severity="confirmSeverity"
        :disabled="busy"
        :loading="busy"
        @click="onConfirm"
      />
    </template>
  </Dialog>
</template>

<style scoped>
.modal-message {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
</style>
