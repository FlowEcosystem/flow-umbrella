<script setup>
const props = defineProps({
  title: { type: String, default: 'Подтвердите действие' },
  icon: { type: String },
  message: { type: String, default: '' },

  confirmText: { type: String, default: 'Подтвердить' },
  cancelText: { type: String, default: 'Отмена' },

  // 'primary' | 'error' | 'warning' | 'success' | 'neutral' | 'ghost'
  confirmVariant: { type: String, default: 'primary' },

  // если true — пока идет confirm, кнопки блокируются
  busyText: { type: String, default: 'Выполняю…' },
})

const emit = defineEmits(['confirm', 'cancel', 'open', 'close'])

const dialogRef = ref(null)
const busy = ref(false)

const confirmBtnClass = computed(() => {
  const v = props.confirmVariant
  return `btn btn-${v}`
})

function open() {
  emit('open')
  dialogRef.value?.showModal()
}

function close() {
  dialogRef.value?.close()
  emit('close')
}

function onCancel() {
  if (busy.value) return
  emit('cancel')
}

async function onConfirm() {
  if (busy.value) return
  busy.value = true
  try {
    await emit('confirm')
  } finally {
    busy.value = false
  }
}

defineExpose({ open, close, busy })
</script>

<template>
  <dialog ref="dialogRef" class="modal">
    <div class="modal-box rounded-3xl p-6">
      <div class="flex gap-2 items-center">
        <component v-if="icon" :is="icon" />
        <h3 class="text-lg font-semibold">{{ title }}</h3>
      </div>

      <p v-if="message" class="mt-2 text-sm text-base-content/70">
        {{ message }}
      </p>

      <!-- кастомный контент -->
      <div v-if="$slots.default" class="mt-3">
        <slot />
      </div>

      <div class="modal-action mt-6 flex gap-3">
        <!-- Cancel -->
        <form method="dialog">
          <button
            type="submit"
            class="btn btn-ghost rounded-2xl"
            :disabled="busy"
            @click="onCancel"
          >
            {{ cancelText }}
          </button>
        </form>

        <!-- Confirm -->
        <form method="dialog">
          <button type="submit" :class="confirmBtnClass" :disabled="busy" @click="onConfirm">
            {{ busy ? busyText : confirmText }}
          </button>
        </form>
      </div>
    </div>

    <!-- backdrop -->
    <form method="dialog" class="modal-backdrop">
      <button aria-label="close" :disabled="busy" @click="onCancel"></button>
    </form>
  </dialog>
</template>
