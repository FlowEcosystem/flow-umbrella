<script setup>
import { X, Plus, Trash2, Check, Search, GripVertical } from 'lucide-vue-next'
import { RULE_LABELS } from '@/domains/policies/usePoliciesPage'
import { useServicesStore } from '@/domains/policies/servicesStore'

const props = defineProps({
  open:    { type: Boolean, required: true },
  target:  { type: Object,  default: null },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: '' },
  kind:    { type: String,  default: 'traffic' },
})

const availableTypes = computed(() =>
  props.kind === 'process' ? ['process'] : ['domain', 'url', 'ip']
)

const emit = defineEmits(['update:open', 'submit'])

const servicesStore = useServicesStore()

const isEdit = computed(() => !!props.target)

// existing categories for autocomplete
const existingCategories = computed(() =>
  [...new Set(servicesStore.items.map(s => s.category))].sort()
)

const emptyForm = () => ({ name: '', category: '', rules: [] })
const form = ref(emptyForm())

watch(() => props.open, v => {
  if (v) {
    form.value = props.target
      ? { name: props.target.name, category: props.target.category, rules: props.target.rules.map(r => ({ ...r })) }
      : emptyForm()
    submitAttempted.value = false
    rulesFilter.value = ''
  }
})

// --- validation ---
const IP_RE = /^(\d{1,3}\.){3}\d{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$/

function ruleError(rule) {
  const v = rule.value.trim()
  if (!v) return 'Обязательное поле'
  if (rule.type === 'ip'      && !IP_RE.test(v)) return 'Неверный формат IP или CIDR'
  if (rule.type === 'url') { try { new URL(v) } catch { return 'Неверный URL' } }
  return null
}

const submitAttempted = ref(false)
const hasInvalidRules = computed(() => form.value.rules.some(r => !!ruleError(r)))
const canSubmit = computed(() => form.value.name.trim() && form.value.category.trim())

function handleSubmit() {
  submitAttempted.value = true
  if (!hasInvalidRules.value && canSubmit.value) {
    emit('submit', {
      name:     form.value.name.trim(),
      category: form.value.category.trim(),
      rules:    form.value.rules,
    })
  }
}

// --- rules ---
const rulesListRef = ref(null)
const rulesFilter  = ref('')

const duplicateValues = computed(() => {
  const seen  = new Set()
  const dupes = new Set()
  for (const r of form.value.rules) {
    const v = r.value.trim()
    if (!v) continue
    if (seen.has(v)) dupes.add(v)
    else seen.add(v)
  }
  return dupes
})

const dragIdx     = ref(null)
const dragOverIdx = ref(null)

function onDragStart(idx) { dragIdx.value = idx }
function onDragOver(e, idx) { e.preventDefault(); dragOverIdx.value = idx }
function onDrop(idx) {
  if (dragIdx.value !== null && dragIdx.value !== idx) {
    const rules = [...form.value.rules]
    const [moved] = rules.splice(dragIdx.value, 1)
    rules.splice(idx, 0, moved)
    form.value.rules = rules
  }
  onDragEnd()
}
function onDragEnd() { dragIdx.value = null; dragOverIdx.value = null }

const hasVisibleRules = computed(() => {
  const q = rulesFilter.value.toLowerCase()
  return !q || form.value.rules.some(r => r.value.toLowerCase().includes(q))
})

async function addRule() {
  rulesFilter.value = ''
  form.value.rules.push({ type: props.kind === 'process' ? 'process' : 'domain', value: '' })
  await nextTick()
  const inputs = rulesListRef.value?.querySelectorAll('input:not([type="hidden"])')
  inputs?.[inputs.length - 1]?.focus()
}

function removeRule(idx) { form.value.rules.splice(idx, 1) }
</script>

<template>
  <Dialog :open="open" @update:open="v => !v && emit('update:open', false)">
    <DialogContent
      :show-close-button="false"
      class="max-w-[560px] p-0 border-white/[0.08] bg-bg-raised gap-0 flex flex-col max-h-[88vh]"
    >
      <!-- header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">
            {{ isEdit ? 'Редактировать сервис' : (kind === 'process' ? 'Новая группа процессов' : 'Новая группа правил') }}
          </DialogTitle>
          <DialogDescription class="text-xs text-fg-subtle mt-0.5">
            {{ isEdit ? target.name : (kind === 'process' ? 'Набор исполняемых файлов для переиспользования в политиках' : 'Домены, URL и IP для переиспользования в политиках трафика') }}
          </DialogDescription>
        </div>
        <button @click="emit('update:open', false)" class="text-fg-subtle hover:text-fg transition-colors">
          <X :size="16" />
        </button>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <div class="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4">

        <!-- name -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Название</label>
          <input
            v-model="form.name"
            placeholder="Telegram"
            class="h-9 w-full rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>

        <!-- category -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Категория</label>
          <input
            v-model="form.category"
            list="category-list"
            placeholder="Мессенджеры"
            class="h-9 w-full rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
          <datalist id="category-list">
            <option v-for="cat in existingCategories" :key="cat" :value="cat" />
          </datalist>
        </div>

        <!-- rules -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-xs text-fg-subtle">Правила</label>
              <span v-if="form.rules.length"
                    class="text-[10px] text-fg-subtle/50 border border-white/[0.08] rounded px-1.5 py-0.5 tabular-nums">
                {{ form.rules.length }}
              </span>
            </div>
            <button type="button" @click="addRule"
                    class="flex items-center gap-1 text-xs text-fg-subtle hover:text-fg transition-colors">
              <Plus :size="11" />
              Добавить
            </button>
          </div>

          <div v-if="!form.rules.length"
               class="rounded-lg border border-dashed border-white/[0.08] py-5 text-center">
            <p class="text-xs text-fg-subtle/50">
              {{ kind === 'process' ? 'Нет процессов — добавьте имена исполняемых файлов' : 'Нет правил — добавьте домены, URL или IP' }}
            </p>
          </div>

          <template v-else>
            <div v-if="form.rules.length >= 4" class="relative">
              <Search :size="11" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
              <input
                v-model="rulesFilter"
                placeholder="Фильтр правил..."
                class="h-7 w-full rounded-md border border-white/[0.06] bg-bg pl-7 pr-7 text-xs text-fg
                       placeholder:text-fg-subtle/30 focus:outline-none focus:border-white/20 transition-colors"
              />
              <button v-if="rulesFilter" type="button" @click="rulesFilter = ''"
                      class="absolute right-2 top-1/2 -translate-y-1/2 text-fg-subtle/40 hover:text-fg-subtle transition-colors">
                <X :size="11" />
              </button>
            </div>

            <div ref="rulesListRef" class="flex flex-col gap-1 max-h-52 overflow-y-auto pr-1">
              <div
                v-for="(rule, idx) in form.rules"
                :key="idx"
                v-show="!rulesFilter || rule.value.toLowerCase().includes(rulesFilter.toLowerCase())"
                draggable="true"
                @dragstart="onDragStart(idx)"
                @dragover="onDragOver($event, idx)"
                @drop="onDrop(idx)"
                @dragend="onDragEnd"
                class="flex items-center gap-1.5 rounded-md transition-colors duration-100"
                :class="dragOverIdx === idx && dragIdx !== idx ? 'bg-white/[0.04] ring-1 ring-white/[0.08]' : ''"
              >
                <div v-show="!rulesFilter"
                     class="cursor-grab active:cursor-grabbing text-fg-subtle/20 hover:text-fg-subtle/50 transition-colors shrink-0 py-2 px-0.5 select-none">
                  <GripVertical :size="12" />
                </div>
                <select
                  v-model="rule.type"
                  class="h-8 rounded-md border border-white/[0.08] bg-bg px-2 text-xs text-fg
                         focus:outline-none focus:border-white/20 transition-colors shrink-0"
                >
                  <option v-for="t in availableTypes" :key="t" :value="t">{{ RULE_LABELS[t] }}</option>
                </select>
                <input
                  v-model="rule.value"
                  :placeholder="rule.type === 'domain' ? 'example.com' : rule.type === 'url' ? 'https://...' : rule.type === 'process' ? 'javaw.exe' : '192.168.0.0/24'"
                  class="h-8 flex-1 rounded-md bg-bg px-3 text-xs text-fg font-mono border
                         placeholder:text-fg-subtle/40 focus:outline-none transition-colors"
                  :class="duplicateValues.has(rule.value.trim()) && rule.value.trim()
                    ? 'border-amber-700/50 focus:border-amber-600/60'
                    : submitAttempted && ruleError(rule)
                      ? 'border-red-700/50 focus:border-red-600/60'
                      : 'border-white/[0.08] focus:border-white/20'"
                  @keydown.enter.prevent="addRule"
                />
                <button type="button" @click="removeRule(idx)"
                        class="p-1.5 rounded text-fg-subtle/40 hover:text-red-400 hover:bg-red-950/30 transition-colors shrink-0">
                  <Trash2 :size="12" />
                </button>
              </div>

              <div v-if="rulesFilter && !hasVisibleRules" class="py-3 text-center text-xs text-fg-subtle/40">
                Ничего не найдено
              </div>
            </div>
          </template>
        </div>

        <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <div class="flex items-center justify-end gap-2 px-6 py-4 shrink-0">
        <button
          @click="emit('update:open', false)"
          class="h-8 px-4 rounded-md text-xs border border-white/[0.08] text-fg-subtle
                 hover:text-fg hover:border-white/20 transition-colors"
        >
          Отмена
        </button>
        <button
          @click="handleSubmit"
          :disabled="loading || !canSubmit"
          class="h-8 px-4 rounded-md text-xs font-medium text-[#1c1917] disabled:opacity-50 transition-opacity"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          {{ loading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>
