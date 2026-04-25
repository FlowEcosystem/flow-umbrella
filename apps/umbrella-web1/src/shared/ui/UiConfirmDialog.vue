<script setup>
import { X, TriangleAlert, OctagonX } from 'lucide-vue-next'

const props = defineProps({
  open:        { type: Boolean, default: false },
  title:       { type: String,  required: true },
  description: { type: String,  default: '' },
  confirmText: { type: String,  default: 'Подтвердить' },
  cancelText:  { type: String,  default: 'Отмена' },
  // 'danger' | 'warning'
  variant:     { type: String,  default: 'danger' },
  loading:     { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'confirm'])

const cfg = computed(() => ({
  danger: {
    icon:       OctagonX,
    iconClass:  'text-red-400',
    iconBg:     'bg-red-950/40 border-red-900/30',
    btnClass:   'bg-red-800 hover:bg-red-700 text-white',
  },
  warning: {
    icon:       TriangleAlert,
    iconClass:  'text-amber-400',
    iconBg:     'bg-amber-950/40 border-amber-900/30',
    btnClass:   'bg-amber-700 hover:bg-amber-600 text-white',
  },
}[props.variant]))
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent
      :show-close-button="false"
      class="max-w-[420px] p-0 border-white/[0.08] bg-bg-raised gap-0"
    >
      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-5">
        <div class="flex items-start gap-4">
          <!-- icon -->
          <div class="w-9 h-9 rounded-lg border flex items-center justify-center shrink-0"
               :class="cfg.iconBg">
            <component :is="cfg.icon" :size="16" :class="cfg.iconClass" />
          </div>
          <!-- text -->
          <div>
            <DialogTitle class="text-base font-medium text-fg leading-tight">{{ title }}</DialogTitle>
            <DialogDescription v-if="description" class="text-sm text-fg-subtle mt-1.5 leading-relaxed">
              {{ description }}
            </DialogDescription>
            <slot name="description" />
          </div>
        </div>
        <button
          @click="$emit('update:open', false)"
          :disabled="loading"
          class="text-fg-subtle hover:text-fg transition-colors ml-3 shrink-0 disabled:opacity-40"
        >
          <X :size="16" />
        </button>
      </div>

      <!-- divider -->
      <div class="h-px bg-white/[0.06] mx-6" />

      <!-- footer -->
      <div class="flex justify-end gap-2 px-6 py-4">
        <button
          @click="$emit('update:open', false)"
          :disabled="loading"
          class="h-9 px-4 rounded-md text-sm text-fg-muted border border-white/[0.08]
                 hover:bg-white/[0.04] transition-colors disabled:opacity-50"
        >
          {{ cancelText }}
        </button>
        <button
          @click="$emit('confirm')"
          :disabled="loading"
          class="h-9 px-4 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          :class="cfg.btnClass"
        >
          {{ loading ? 'Выполнение...' : confirmText }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>
