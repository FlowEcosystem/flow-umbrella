<script setup>
import { X } from 'lucide-vue-next'
import { AGENT_STATUSES, STATUS_LABELS } from '@/domains/agents/agents.utils'

const props = defineProps({
  open:    Boolean,
  form:    Object,
  loading: Boolean,
  error:   String,
})
const emit = defineEmits(['update:open', 'submit'])
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent :show-close-button="false" class="max-w-[480px] p-0 border-white/[0.08] bg-bg-raised gap-0">

      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06]">
        <div>
          <DialogTitle class="text-base font-medium text-fg">Редактировать агента</DialogTitle>
          <DialogDescription class="text-sm text-fg-subtle mt-0.5">Обновление hostname, статуса и заметок.</DialogDescription>
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
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Hostname</label>
          <Input v-model="form.hostname" placeholder="srv-app-01"
                 class="bg-bg border-white/[0.08] focus-visible:border-accent/50 focus-visible:ring-accent/20" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Статус</label>
          <div class="flex gap-1.5 flex-wrap">
            <button
              v-for="s in AGENT_STATUSES" :key="s"
              @click="form.status = s"
              class="h-8 px-3 rounded-md text-xs border transition-colors"
              :class="form.status === s
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
            >
              {{ STATUS_LABELS[s] }}
            </button>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Заметки</label>
          <textarea v-model="form.notes" rows="3" placeholder="Дополнительный контекст..."
                    class="w-full rounded-md border border-white/[0.08] bg-bg px-3 py-2 text-sm text-fg
                           placeholder:text-fg-subtle/40 focus:outline-none focus:border-accent/50
                           transition-colors resize-none" />
        </div>
      </div>

      <!-- footer -->
      <div class="flex justify-end gap-2 px-6 pb-6">
        <button @click="$emit('update:open', false)" :disabled="loading"
                class="h-9 px-4 rounded-md text-sm text-fg-muted border border-white/[0.08]
                       hover:bg-white/[0.04] transition-colors disabled:opacity-50">
          Отмена
        </button>
        <button @click="$emit('submit')" :disabled="loading || !form.hostname"
                class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
                style="background: linear-gradient(135deg, #c4683a, #d4785a)">
          {{ loading ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>

    </DialogContent>
  </Dialog>
</template>
