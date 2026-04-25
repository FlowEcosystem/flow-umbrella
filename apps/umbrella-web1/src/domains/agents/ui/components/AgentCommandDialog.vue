<script setup>
import { X } from 'lucide-vue-next'

const props = defineProps({
  open:         Boolean,
  commandTypes: Array,
  typeLabels:   Object,
  type:         String,
  payload:      String,
  loading:      Boolean,
  error:        String,
})
const emit = defineEmits(['update:open', 'update:type', 'update:payload', 'submit'])
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent :show-close-button="false" class="max-w-[480px] p-0 border-white/[0.08] bg-bg-raised gap-0">

      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06]">
        <div>
          <DialogTitle class="text-base font-medium text-fg">Отправить команду</DialogTitle>
          <DialogDescription class="text-sm text-fg-subtle mt-0.5">
            Команда будет поставлена в очередь агенту.
          </DialogDescription>
        </div>
        <button @click="$emit('update:open', false)"
                class="text-fg-subtle hover:text-fg transition-colors mt-0.5">
          <X :size="18" />
        </button>
      </div>

      <!-- body -->
      <div class="px-6 py-5 flex flex-col gap-4">

        <div v-if="error"
             class="text-xs text-red-400 bg-red-950/30 border border-red-900/30 rounded-lg px-3 py-2.5">
          {{ error }}
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Тип команды</label>
          <div class="flex gap-1.5 flex-wrap">
            <button
              v-for="t in commandTypes" :key="t"
              @click="$emit('update:type', t)"
              class="h-8 px-3 rounded-md text-xs border transition-colors"
              :class="type === t
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
            >
              {{ typeLabels[t] ?? t }}
            </button>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">
            Payload <span class="normal-case font-normal">(JSON, необязательно)</span>
          </label>
          <textarea
            :value="payload"
            rows="3"
            placeholder='{"key": "value"}'
            @input="$emit('update:payload', $event.target.value)"
            class="w-full rounded-md border border-white/[0.08] bg-bg px-3 py-2 text-sm text-fg font-mono
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-accent/50
                   transition-colors resize-none"
          />
        </div>

      </div>

      <!-- footer -->
      <div class="flex justify-end gap-2 px-6 pb-6">
        <button @click="$emit('update:open', false)" :disabled="loading"
                class="h-9 px-4 rounded-md text-sm text-fg-muted border border-white/[0.08]
                       hover:bg-white/[0.04] transition-colors disabled:opacity-50">
          Отмена
        </button>
        <button @click="$emit('submit')" :disabled="loading"
                class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
                style="background: linear-gradient(135deg, #c4683a, #d4785a)">
          {{ loading ? 'Отправка...' : 'Отправить' }}
        </button>
      </div>

    </DialogContent>
  </Dialog>
</template>
