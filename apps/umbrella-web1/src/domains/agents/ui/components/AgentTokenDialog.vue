<script setup>
import { X, Copy, Check } from 'lucide-vue-next'
import { formatDate } from '@/domains/agents/agents.utils'

const props = defineProps({
  open:    Boolean,
  data:    Object,
  copied:  Boolean,
})
const emit = defineEmits(['update:open', 'copy'])
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent :show-close-button="false" class="max-w-[520px] p-0 border-white/[0.08] bg-bg-raised gap-0">

      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06]">
        <div>
          <DialogTitle class="text-base font-medium text-fg">Enrollment token</DialogTitle>
          <DialogDescription class="text-sm text-fg-subtle mt-0.5">Токен показывается один раз — сохраните его.</DialogDescription>
        </div>
        <button @click="$emit('update:open', false)"
                class="text-fg-subtle hover:text-fg transition-colors mt-0.5">
          <X :size="18" />
        </button>
      </div>

      <div v-if="data" class="px-6 py-5 flex flex-col gap-4">

        <!-- warning -->
        <div class="flex gap-3 bg-amber-950/30 border border-amber-900/30 rounded-xl px-4 py-3">
          <svg class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" viewBox="0 0 16 16" fill="none">
            <path d="M8 2L14.9 14H1.1L8 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
            <path d="M8 6v3M8 11v.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          <p class="text-xs text-amber-400 leading-relaxed">
            После закрытия этого окна токен не будет доступен повторно. Для получения нового используйте перевыпуск.
          </p>
        </div>

        <!-- token block -->
        <div class="rounded-xl border border-white/[0.06] bg-bg overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06]">
            <span class="text-xs text-fg-subtle font-mono uppercase tracking-wider">Token</span>
            <button @click="$emit('copy')"
                    class="flex items-center gap-1.5 text-xs transition-colors px-2 py-1 rounded"
                    :class="copied ? 'text-emerald-400' : 'text-fg-subtle hover:text-fg'">
              <component :is="copied ? Check : Copy" :size="13" />
              {{ copied ? 'Скопировано' : 'Скопировать' }}
            </button>
          </div>
          <div class="px-4 py-3">
            <code class="text-xs text-accent font-mono break-all leading-relaxed">
              {{ data.enrollment_token }}
            </code>
          </div>
        </div>

        <!-- meta -->
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-lg border border-white/[0.06] bg-bg px-4 py-3">
            <p class="text-[11px] text-fg-subtle uppercase tracking-wider mb-1">Hostname</p>
            <p class="text-sm text-fg font-mono">{{ data.agent.hostname }}</p>
          </div>
          <div class="rounded-lg border border-white/[0.06] bg-bg px-4 py-3">
            <p class="text-[11px] text-fg-subtle uppercase tracking-wider mb-1">Истекает</p>
            <p class="text-sm text-fg font-mono">{{ formatDate(data.enrollment_token_expires_at) }}</p>
          </div>
        </div>
      </div>

      <!-- footer -->
      <div class="flex justify-end px-6 pb-6">
        <button @click="$emit('update:open', false)"
                class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917]"
                style="background: linear-gradient(135deg, #c4683a, #d4785a)">
          Закрыть
        </button>
      </div>

    </DialogContent>
  </Dialog>
</template>
