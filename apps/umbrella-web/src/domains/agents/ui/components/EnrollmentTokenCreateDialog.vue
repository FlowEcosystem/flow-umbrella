<script setup>
import { X, Copy, Check, Trash2, Terminal } from 'lucide-vue-next'
import { formatDate } from '@/domains/agents/agents.utils'
import { colorDotStyle, fallbackColor } from '@/domains/groups/groups.utils'

const props = defineProps({
  open:         Boolean,
  form:         Object,
  loading:      Boolean,
  error:        String,
  created:      Object,   // EnrollmentTokenCreated: { token: EnrollmentTokenRead, raw_token: str }
  copied:       Boolean,
  cmdCopied:    Boolean,
  tokenList:    Array,
  listLoading:  Boolean,
  groups:       { type: Array, default: () => [] },
  groupsLoading: Boolean,
})

defineEmits(['update:open', 'submit', 'copy', 'copy-cmd', 'revoke'])

const expiresOptions = [
  { label: '1 день',  value: 1  },
  { label: '7 дней',  value: 7  },
  { label: '30 дней', value: 30 },
]

const serverUrl = import.meta.env.VITE_API_BASE_URL ?? window.location.origin

const installCmd = computed(() => {
  if (!props.created) return ''
  return `umbrella-agent --token ${props.created.raw_token} --server ${serverUrl}`
})

const tokenFilter = ref('active')  // 'active' | 'used' | 'all'

const now = new Date()

const filteredTokenList = computed(() => {
  if (!props.tokenList) return []
  return props.tokenList.filter(t => {
    const expired = new Date(t.expires_at) < now
    const used = t.used_at !== null || (t.max_uses !== null && t.uses_count >= t.max_uses)
    if (tokenFilter.value === 'active') return !expired && !used
    if (tokenFilter.value === 'used')   return used || expired
    return true
  })
})
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent :show-close-button="false"
                   class="max-w-[540px] p-0 border-white/[0.08] bg-bg-raised gap-0 max-h-[90vh] flex flex-col">

      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06] shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">
            {{ created ? 'Enrollment token создан' : 'Enrollment tokens' }}
          </DialogTitle>
          <DialogDescription class="text-sm text-fg-subtle mt-0.5">
            {{ created
              ? 'Токен показывается один раз — скопируйте команду установки.'
              : 'Создайте токен для первичной регистрации агента.' }}
          </DialogDescription>
        </div>
        <button @click="$emit('update:open', false)"
                class="text-fg-subtle hover:text-fg transition-colors mt-0.5">
          <X :size="18" />
        </button>
      </div>

      <div class="overflow-y-auto flex-1 flex flex-col">

        <!-- ── step 1: create form ───────────────────────────── -->
        <div v-if="!created" class="px-6 py-5 flex flex-col gap-4">

          <div v-if="error"
               class="text-xs text-red-400 bg-red-950/30 border border-red-900/30 rounded-lg px-3 py-2.5">
            {{ error }}
          </div>

          <!-- note -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Заметка (необязательно)</label>
            <Input v-model="form.note" placeholder="Офис / Серверная / Хост-01..."
                   class="bg-bg border-white/[0.08] focus-visible:border-accent/50 focus-visible:ring-accent/20" />
          </div>

          <!-- expires -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Срок действия</label>
            <div class="flex gap-1.5">
              <button
                v-for="opt in expiresOptions" :key="opt.value"
                @click="form.expires_in_days = opt.value"
                class="h-8 px-3 rounded-md text-xs border transition-colors"
                :class="form.expires_in_days === opt.value
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- max uses -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">
              Лимит использований
              <span class="normal-case font-normal">(пусто = одноразовый)</span>
            </label>
            <div class="flex gap-1.5 items-center">
              <button
                class="h-8 px-3 rounded-md text-xs border transition-colors"
                :class="form.max_uses === null
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
                @click="form.max_uses = null"
              >
                1×
              </button>
              <button
                v-for="n in [5, 10, 50, 100]" :key="n"
                @click="form.max_uses = n"
                class="h-8 px-3 rounded-md text-xs border transition-colors"
                :class="form.max_uses === n
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
              >
                {{ n }}×
              </button>
            </div>
          </div>

          <!-- group -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">
              Группа <span class="normal-case font-normal">(агент добавится автоматически)</span>
            </label>
            <div v-if="groupsLoading" class="text-xs text-fg-subtle/50">Загрузка групп...</div>
            <div v-else-if="!groups.length" class="text-xs text-fg-subtle/50">Нет доступных групп</div>
            <div v-else class="flex flex-wrap gap-1.5">
              <button
                class="h-8 px-3 rounded-md text-xs border transition-colors"
                :class="!form.group_id
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
                @click="form.group_id = null"
              >
                Без группы
              </button>
              <button
                v-for="g in groups" :key="g.id"
                @click="form.group_id = g.id"
                class="h-8 px-3 rounded-md text-xs border transition-colors flex items-center gap-1.5"
                :class="form.group_id === g.id
                  ? 'border-accent/50 bg-accent/10 text-accent'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
              >
                <span class="w-1.5 h-1.5 rounded-full shrink-0"
                      :style="colorDotStyle(g.color || fallbackColor(g.name))" />
                {{ g.name }}
              </button>
            </div>
          </div>
        </div>

        <!-- ── step 2: created token + install command ────────── -->
        <div v-else class="px-6 py-5 flex flex-col gap-4">

          <!-- warning -->
          <div class="flex gap-3 bg-amber-950/30 border border-amber-900/30 rounded-xl px-4 py-3">
            <svg class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" viewBox="0 0 16 16" fill="none">
              <path d="M8 2L14.9 14H1.1L8 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
              <path d="M8 6v3M8 11v.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
            <p class="text-xs text-amber-400 leading-relaxed">
              После закрытия этого окна токен не будет доступен повторно.
            </p>
          </div>

          <!-- install command — primary CTA -->
          <div class="rounded-xl border border-white/[0.06] bg-bg overflow-hidden">
            <div class="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06]">
              <div class="flex items-center gap-2">
                <Terminal :size="12" class="text-fg-subtle/60" />
                <span class="text-xs text-fg-subtle font-mono uppercase tracking-wider">Команда установки</span>
              </div>
              <button @click="$emit('copy-cmd')"
                      class="flex items-center gap-1.5 text-xs transition-colors px-2 py-1 rounded"
                      :class="cmdCopied ? 'text-emerald-400' : 'text-fg-subtle hover:text-fg'">
                <component :is="cmdCopied ? Check : Copy" :size="13" />
                {{ cmdCopied ? 'Скопировано' : 'Скопировать' }}
              </button>
            </div>
            <div class="px-4 py-3">
              <code class="text-xs text-fg font-mono break-all leading-relaxed">{{ installCmd }}</code>
            </div>
          </div>

          <!-- raw token (secondary) -->
          <div class="rounded-xl border border-white/[0.06] bg-bg overflow-hidden">
            <div class="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06]">
              <span class="text-xs text-fg-subtle/70 font-mono uppercase tracking-wider">Токен</span>
              <button @click="$emit('copy')"
                      class="flex items-center gap-1.5 text-xs transition-colors px-2 py-1 rounded"
                      :class="copied ? 'text-emerald-400' : 'text-fg-subtle hover:text-fg'">
                <component :is="copied ? Check : Copy" :size="13" />
                {{ copied ? 'Скопировано' : 'Скопировать' }}
              </button>
            </div>
            <div class="px-4 py-3">
              <code class="text-xs text-accent font-mono break-all leading-relaxed">{{ created.raw_token }}</code>
            </div>
          </div>

          <!-- meta -->
          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-lg border border-white/[0.06] bg-bg px-4 py-3">
              <p class="text-[11px] text-fg-subtle uppercase tracking-wider mb-1">Заметка</p>
              <p class="text-sm text-fg">{{ created.token.note || '—' }}</p>
            </div>
            <div class="rounded-lg border border-white/[0.06] bg-bg px-4 py-3">
              <p class="text-[11px] text-fg-subtle uppercase tracking-wider mb-1">Истекает</p>
              <p class="text-sm text-fg font-mono">{{ formatDate(created.token.expires_at) }}</p>
            </div>
          </div>
        </div>

        <!-- ── tokens list (only in create form) ────────────── -->
        <div v-if="!created" class="border-t border-white/[0.06]">

          <!-- tabs -->
          <div class="px-6 pt-3 pb-2 flex items-center gap-1">
            <button
              v-for="tab in [{ v: 'active', l: 'Активные' }, { v: 'used', l: 'Использованные' }, { v: 'all', l: 'Все' }]"
              :key="tab.v"
              @click="tokenFilter = tab.v"
              class="h-6 px-2.5 rounded-md text-[11px] transition-colors"
              :class="tokenFilter === tab.v
                ? 'bg-white/[0.08] text-fg'
                : 'text-fg-subtle/60 hover:text-fg-subtle'"
            >
              {{ tab.l }}
            </button>
            <Loader2 v-if="listLoading" :size="11" class="animate-spin text-fg-subtle/40 ml-1" />
            <span v-if="filteredTokenList.length" class="text-[11px] text-fg-subtle/40 tabular-nums ml-auto">
              {{ filteredTokenList.length }}
            </span>
          </div>

          <div v-if="listLoading && !tokenList?.length" class="px-6 pb-4 text-xs text-fg-subtle/50">
            Загрузка...
          </div>

          <div v-else-if="!filteredTokenList.length" class="px-6 pb-5 text-xs text-fg-subtle/50">
            {{ tokenFilter === 'active' ? 'Нет активных токенов' : 'Нет токенов' }}
          </div>

          <div v-else class="divide-y divide-white/[0.04] pb-2">
            <div
              v-for="tok in filteredTokenList" :key="tok.id"
              class="group/tok flex items-center gap-3 px-6 py-2.5 hover:bg-white/[0.02] transition-colors"
            >
              <span v-if="tok.group_id"
                    class="w-1.5 h-1.5 rounded-full shrink-0"
                    :style="colorDotStyle(groups.find(g => g.id === tok.group_id)?.color || fallbackColor(groups.find(g => g.id === tok.group_id)?.name ?? ''))" />
              <div class="flex-1 min-w-0">
                <p class="text-xs text-fg truncate">{{ tok.note || '(без заметки)' }}</p>
                <p class="text-xs text-fg-subtle/50 mt-0.5 tabular-nums flex items-center gap-2">
                  <span>до {{ formatDate(tok.expires_at) }}</span>
                  <span v-if="tok.max_uses !== null"
                        class="text-fg-subtle/70">
                    {{ tok.uses_count }}/{{ tok.max_uses }} исп.
                  </span>
                  <span v-else-if="tok.used_at" class="text-emerald-400/70">использован</span>
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
