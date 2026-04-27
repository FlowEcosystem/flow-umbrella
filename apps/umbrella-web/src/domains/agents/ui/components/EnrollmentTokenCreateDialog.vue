<script setup>
import { X, Copy, Check, Trash2, Loader2 } from 'lucide-vue-next'
import { formatDate } from '@/domains/agents/agents.utils'

defineProps({
  open:       Boolean,
  form:       Object,
  loading:    Boolean,
  error:      String,
  created:    Object,
  copied:     Boolean,
  tokenList:  Array,
  listLoading: Boolean,
})

defineEmits(['update:open', 'submit', 'copy', 'revoke'])

const expiresOptions = [
  { label: '1 час',   value: 1   },
  { label: '8 часов', value: 8   },
  { label: '24 часа', value: 24  },
  { label: '7 дней',  value: 168 },
]
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent :show-close-button="false" class="max-w-[520px] p-0 border-white/[0.08] bg-bg-raised gap-0 max-h-[90vh] flex flex-col">

      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06] shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">
            {{ created ? 'Enrollment token создан' : 'Enrollment tokens' }}
          </DialogTitle>
          <DialogDescription class="text-sm text-fg-subtle mt-0.5">
            {{ created ? 'Токен показывается один раз — сохраните его.' : 'Создайте токен для первичной регистрации агента.' }}
          </DialogDescription>
        </div>
        <button @click="$emit('update:open', false)"
                class="text-fg-subtle hover:text-fg transition-colors mt-0.5">
          <X :size="18" />
        </button>
      </div>

      <div class="overflow-y-auto flex-1 flex flex-col">

        <!-- step 1: create form -->
        <div v-if="!created" class="px-6 py-5 flex flex-col gap-4">

          <div v-if="error"
               class="text-xs text-red-400 bg-red-950/30 border border-red-900/30 rounded-lg px-3 py-2.5">
            {{ error }}
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Заметка (необязательно)</label>
            <Input v-model="form.note" placeholder="Офис / Серверная / Хост-01..."
                   class="bg-bg border-white/[0.08] focus-visible:border-accent/50 focus-visible:ring-accent/20" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Срок действия</label>
            <div class="flex gap-1.5 flex-wrap">
              <button
                v-for="opt in expiresOptions" :key="opt.value"
                @click="form.expires_in_hours = opt.value"
                class="h-8 px-3 rounded-md text-xs border transition-colors"
                :class="form.expires_in_hours === opt.value
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- step 2: show created token -->
        <div v-else class="px-6 py-5 flex flex-col gap-4">

          <div class="flex gap-3 bg-amber-950/30 border border-amber-900/30 rounded-xl px-4 py-3">
            <svg class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" viewBox="0 0 16 16" fill="none">
              <path d="M8 2L14.9 14H1.1L8 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
              <path d="M8 6v3M8 11v.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
            <p class="text-xs text-amber-400 leading-relaxed">
              После закрытия этого окна токен не будет доступен повторно.
            </p>
          </div>

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
              <code class="text-xs text-accent font-mono break-all leading-relaxed">{{ created.token }}</code>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-lg border border-white/[0.06] bg-bg px-4 py-3">
              <p class="text-[11px] text-fg-subtle uppercase tracking-wider mb-1">Заметка</p>
              <p class="text-sm text-fg">{{ created.note || '—' }}</p>
            </div>
            <div class="rounded-lg border border-white/[0.06] bg-bg px-4 py-3">
              <p class="text-[11px] text-fg-subtle uppercase tracking-wider mb-1">Истекает</p>
              <p class="text-sm text-fg font-mono">{{ formatDate(created.expires_at) }}</p>
            </div>
          </div>
        </div>

        <!-- active tokens list -->
        <div v-if="!created" class="border-t border-white/[0.06]">
          <div class="px-6 py-3 flex items-center gap-2">
            <span class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Активные токены</span>
            <Loader2 v-if="listLoading" :size="11" class="animate-spin text-fg-subtle/50" />
          </div>

          <div v-if="!listLoading && !tokenList?.length"
               class="px-6 pb-5 text-xs text-fg-subtle/50">
            Нет активных токенов
          </div>

          <div v-else class="divide-y divide-white/[0.04]">
            <div
              v-for="tok in tokenList" :key="tok.id"
              class="group/tok flex items-center gap-3 px-6 py-2.5 hover:bg-white/[0.02] transition-colors"
            >
              <div class="flex-1 min-w-0">
                <p class="text-xs text-fg truncate">{{ tok.note || '(без заметки)' }}</p>
                <p class="text-xs text-fg-subtle/50 mt-0.5 tabular-nums">
                  до {{ formatDate(tok.expires_at) }}
                  <span v-if="tok.used_at" class="text-emerald-400/70 ml-2">использован</span>
                </p>
              </div>
              <Tooltip>
                <TooltipTrigger as-child>
                  <button
                    @click="$emit('revoke', tok.id)"
                    class="opacity-0 group-hover/tok:opacity-100 p-1.5 rounded text-fg-subtle/40
                           hover:text-red-400 hover:bg-red-950/30 transition-all shrink-0"
                  >
                    <Trash2 :size="12" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Отозвать токен</TooltipContent>
              </Tooltip>
            </div>
          </div>
        </div>

      </div>

      <!-- footer -->
      <div class="flex justify-end gap-2 px-6 pb-6 pt-4 border-t border-white/[0.06] shrink-0">
        <template v-if="!created">
          <button @click="$emit('update:open', false)" :disabled="loading"
                  class="h-9 px-4 rounded-md text-sm text-fg-muted border border-white/[0.08]
                         hover:bg-white/[0.04] transition-colors disabled:opacity-50">
            Отмена
          </button>
          <button @click="$emit('submit')" :disabled="loading"
                  class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed"
                  style="background: linear-gradient(135deg, #c4683a, #d4785a)">
            {{ loading ? 'Создание...' : 'Создать токен' }}
          </button>
        </template>
        <button v-else @click="$emit('update:open', false)"
                class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917]"
                style="background: linear-gradient(135deg, #c4683a, #d4785a)">
          Закрыть
        </button>
      </div>

    </DialogContent>
  </Dialog>
</template>
