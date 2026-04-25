<script setup>
import { X, Plus, Trash2, Zap, Check, Search, GripVertical, Loader2 } from 'lucide-vue-next'
import { RULE_TYPES, RULE_LABELS, ACTION_LABELS } from '@/domains/policies/usePoliciesPage'
import { useServicesStore } from '@/domains/policies/servicesStore'

const props = defineProps({
  open:    { type: Boolean, required: true },
  form:    { type: Object,  required: true },
  target:  { type: Object,  default: null },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: '' },
})

const emit = defineEmits(['update:open', 'submit'])

const isEdit = computed(() => !!props.target)

const servicesStore = useServicesStore()
onMounted(() => { if (!servicesStore.items.length) servicesStore.fetch() })

// --- rule format validation ---
const IP_RE = /^(\d{1,3}\.){3}\d{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$/

function ruleError(rule) {
  const v = rule.value.trim()
  if (!v) return 'Обязательное поле'
  if (rule.type === 'ip'      && !IP_RE.test(v)) return 'Неверный формат IP или CIDR'
  if (rule.type === 'url') { try { new URL(v) } catch { return 'Неверный URL' } }
  return null
}

// --- submit ---
const submitAttempted = ref(false)
const hasInvalidRules = computed(() => props.form.custom_rules.some(r => !!ruleError(r)))
function handleSubmit() {
  submitAttempted.value = true
  if (!hasInvalidRules.value) emit('submit')
}

// --- unsaved changes guard ---
const originalForm     = ref(null)
const closeConfirmOpen = ref(false)

function snapshot() {
  return JSON.stringify({
    name: props.form.name, description: props.form.description,
    action: props.form.action, is_active: props.form.is_active,
    service_ids: [...props.form.service_ids].sort(),
    custom_rules: props.form.custom_rules,
  })
}

const isDirty = computed(() => !!originalForm.value && snapshot() !== originalForm.value)

watch(() => props.open, async v => {
  if (v) { await nextTick(); originalForm.value = snapshot() }
  else   { submitAttempted.value = false; originalForm.value = null; rulesFilter.value = '' }
})

function handleClose() {
  if (isDirty.value) { closeConfirmOpen.value = true; return }
  emit('update:open', false)
}
function confirmClose() {
  closeConfirmOpen.value = false
  emit('update:open', false)
}

// --- service preset panel ---
const presetOpen = ref(false)

// preset search — cross-category when query present
const presetSearch = ref('')
watch(presetOpen, v => { if (!v) presetSearch.value = '' })

const shownGrouped = computed(() => {
  const q = presetSearch.value.trim().toLowerCase()
  if (!q) return trafficGrouped.value
  const filtered = trafficServices.value.filter(s => s.name.toLowerCase().includes(q))
  return filtered.length ? [{ label: 'Результаты поиска', services: filtered }] : []
})

// preset — only traffic services
const trafficServices = computed(() =>
  servicesStore.items.filter(s => (s.kind ?? 'traffic') === 'traffic')
)
const trafficGrouped = computed(() => {
  const map = new Map()
  for (const s of trafficServices.value) {
    if (!map.has(s.category)) map.set(s.category, [])
    map.get(s.category).push(s)
  }
  return [...map.entries()].map(([label, services]) => ({ label, services }))
})

const addedServiceIds = computed(() => new Set(props.form.service_ids))

function toggleService(service) {
  const id = service.id
  if (addedServiceIds.value.has(id)) {
    props.form.service_ids = props.form.service_ids.filter(x => x !== id)
  } else {
    props.form.service_ids = [...props.form.service_ids, id]
  }
}

// --- manual rules (custom_rules) ---
const rulesListRef = ref(null)
const rulesFilter  = ref('')

// duplicate detection
const duplicateValues = computed(() => {
  const seen  = new Set()
  const dupes = new Set()
  for (const r of props.form.custom_rules) {
    const v = r.value.trim()
    if (!v) continue
    if (seen.has(v)) dupes.add(v)
    else seen.add(v)
  }
  return dupes
})

// drag-and-drop reorder
const dragIdx     = ref(null)
const dragOverIdx = ref(null)

function onDragStart(idx) { dragIdx.value = idx }
function onDragOver(e, idx) { e.preventDefault(); dragOverIdx.value = idx }
function onDrop(idx) {
  if (dragIdx.value !== null && dragIdx.value !== idx) {
    const rules = [...props.form.custom_rules]
    const [moved] = rules.splice(dragIdx.value, 1)
    rules.splice(idx, 0, moved)
    props.form.custom_rules = rules
  }
  onDragEnd()
}
function onDragEnd() { dragIdx.value = null; dragOverIdx.value = null }

const hasVisibleRules = computed(() => {
  const q = rulesFilter.value.toLowerCase()
  return !q || props.form.custom_rules.some(r => r.value.toLowerCase().includes(q))
})

async function addRule() {
  rulesFilter.value = ''
  props.form.custom_rules.push({ type: 'domain', value: '' })
  await nextTick()
  const inputs = rulesListRef.value?.querySelectorAll('input:not([type="hidden"])')
  inputs?.[inputs.length - 1]?.focus()
}

function removeRule(idx) {
  props.form.custom_rules.splice(idx, 1)
}
</script>

<template>
  <Dialog :open="open" @update:open="v => !v ? handleClose() : emit('update:open', v)">
    <DialogContent
      :show-close-button="false"
      class="max-w-[600px] p-0 border-white/[0.08] bg-bg-raised gap-0 flex flex-col max-h-[92vh]"
    >
      <!-- header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">
            {{ isEdit ? 'Редактировать политику' : 'Новая политика трафика' }}
          </DialogTitle>
          <DialogDescription class="text-xs text-fg-subtle mt-0.5">
            {{ isEdit ? target.name : 'Блокировать или разрешить сетевой трафик по доменам, URL и IP' }}
          </DialogDescription>
        </div>
        <button @click="handleClose" class="text-fg-subtle hover:text-fg transition-colors">
          <X :size="16" />
        </button>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <!-- body -->
      <div class="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4">

        <!-- name -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Название</label>
          <input
            v-model="form.name"
            placeholder="Блокировка социальных сетей"
            class="h-9 w-full rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>

        <!-- description -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Описание <span class="text-fg-subtle/50">(необязательно)</span></label>
          <textarea
            v-model="form.description"
            placeholder="Краткое описание назначения политики"
            rows="2"
            class="w-full rounded-md border border-white/[0.08] bg-bg px-3 py-2 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors resize-none"
          />
        </div>

        <!-- action + active -->
        <div class="flex gap-3">
          <div class="flex flex-col gap-1.5 flex-1">
            <label class="text-xs text-fg-subtle">Действие</label>
            <div class="flex gap-1.5">
              <button
                v-for="a in ['block', 'allow']" :key="a"
                type="button"
                @click="form.action = a"
                class="flex-1 h-9 rounded-md text-sm border transition-all duration-150"
                :class="form.action === a
                  ? a === 'block'
                    ? 'border-red-700/50 bg-red-950/40 text-red-400'
                    : 'border-emerald-700/50 bg-emerald-950/40 text-emerald-400'
                  : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
              >
                {{ ACTION_LABELS[a] }}
              </button>
            </div>
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-fg-subtle">Активна</label>
            <div class="h-9 flex items-center">
              <button
                type="button"
                @click="form.is_active = !form.is_active"
                class="relative w-8 h-[18px] rounded-full border transition-all duration-200"
                :class="form.is_active
                  ? 'bg-accent/20 border-accent/50'
                  : 'bg-white/[0.04] border-white/[0.12]'"
              >
                <span
                  class="absolute top-[2px] w-[13px] h-[13px] rounded-full transition-all duration-200"
                  :class="form.is_active ? 'left-[18px] bg-accent' : 'left-[2px] bg-fg-subtle/40'"
                />
              </button>
            </div>
          </div>
        </div>

        <!-- services section -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-xs text-fg-subtle">Группы правил</label>
              <span v-if="form.service_ids.length"
                    class="text-[10px] text-fg-subtle/50 border border-white/[0.08] rounded px-1.5 py-0.5 tabular-nums">
                {{ form.service_ids.length }}
              </span>
            </div>
            <button
              type="button"
              @click="presetOpen = !presetOpen"
              class="flex items-center gap-1.5 h-7 px-2.5 rounded-md text-xs border transition-all duration-150"
              :class="presetOpen
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
            >
              <Zap :size="11" />
              Выбрать группы
            </button>
          </div>

          <!-- selected services chips -->
          <div v-if="form.service_ids.length && !presetOpen" class="flex flex-wrap gap-1.5">
            <span
              v-for="id in form.service_ids" :key="id"
              class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border
                     border-accent/30 bg-accent/10 text-accent"
            >
              {{ servicesStore.items.find(s => s.id === id)?.name ?? id }}
              <button type="button" @click="props.form.service_ids = props.form.service_ids.filter(x => x !== id)"
                      class="ml-0.5 opacity-60 hover:opacity-100 transition-opacity">
                <X :size="10" />
              </button>
            </span>
          </div>

          <!-- service preset panel -->
          <Transition
            enter-active-class="transition-all duration-150 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            leave-active-class="transition-all duration-100 ease-in"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <div v-if="presetOpen"
                 class="rounded-xl border border-white/[0.08] bg-bg overflow-hidden">

              <!-- loading -->
              <div v-if="servicesStore.isLoading"
                   class="flex items-center justify-center gap-2 py-8 text-xs text-fg-subtle/50">
                <Loader2 :size="14" class="animate-spin" />
                Загрузка сервисов...
              </div>

              <template v-else-if="servicesStore.items.length">
                <!-- search -->
                <div class="px-2 pt-2">
                  <div class="relative">
                    <Search :size="11" class="absolute left-2 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
                    <input
                      v-model="presetSearch"
                      placeholder="Поиск сервиса..."
                      class="h-6 w-full rounded border border-white/[0.06] bg-bg/60 pl-6 pr-2 text-xs text-fg
                             placeholder:text-fg-subtle/30 focus:outline-none focus:border-white/20 transition-colors"
                    />
                  </div>
                </div>

                <!-- grouped services -->
                <div class="p-2 flex flex-col gap-3 max-h-64 overflow-y-auto">
                  <div v-if="!shownGrouped.length" class="py-4 text-center text-xs text-fg-subtle/40">
                    Ничего не найдено
                  </div>
                  <div v-for="group in shownGrouped" :key="group.label">
                    <p class="text-[10px] text-fg-subtle/40 uppercase tracking-wider mb-1 px-0.5">{{ group.label }}</p>
                    <div class="grid grid-cols-3 gap-1">
                      <button
                        v-for="service in group.services"
                        :key="service.id"
                        type="button"
                        @click="toggleService(service)"
                        class="flex items-center gap-2 h-8 px-2.5 rounded-md text-xs border transition-all duration-150 text-left"
                        :class="addedServiceIds.has(service.id)
                          ? 'border-accent/40 bg-accent/10 text-accent'
                          : 'border-white/[0.06] text-fg-subtle hover:text-fg hover:border-white/[0.12] hover:bg-white/[0.03]'"
                      >
                        <Check v-if="addedServiceIds.has(service.id)" :size="11" class="shrink-0" />
                        <span v-else class="w-[11px] shrink-0" />
                        <span class="truncate">{{ service.name }}</span>
                        <span class="ml-auto text-[10px] opacity-50 tabular-nums shrink-0">{{ service.rules_count }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </template>

              <div v-else class="py-8 text-center text-xs text-fg-subtle/40">
                Нет групп трафика — создайте их во вкладке «Сервисы»
              </div>
            </div>
          </Transition>
        </div>

        <!-- custom rules section -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-xs text-fg-subtle">Дополнительные правила</label>
              <span v-if="form.custom_rules.length"
                    class="text-[10px] text-fg-subtle/50 border border-white/[0.08] rounded px-1.5 py-0.5 tabular-nums">
                {{ form.custom_rules.length }}
              </span>
            </div>
            <button
              type="button"
              @click="addRule"
              class="flex items-center gap-1 text-xs text-fg-subtle hover:text-fg transition-colors"
            >
              <Plus :size="11" />
              Добавить
            </button>
          </div>

          <div v-if="!form.custom_rules.length"
               class="rounded-lg border border-dashed border-white/[0.08] py-5 text-center">
            <p class="text-xs text-fg-subtle/50">Нет дополнительных правил</p>
          </div>

          <template v-else>
            <!-- rules search — shown when 4+ rules -->
            <div v-if="form.custom_rules.length >= 4" class="relative">
              <Search :size="11" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
              <input
                v-model="rulesFilter"
                placeholder="Фильтр правил..."
                class="h-7 w-full rounded-md border border-white/[0.06] bg-bg pl-7 pr-7 text-xs text-fg
                       placeholder:text-fg-subtle/30 focus:outline-none focus:border-white/20 transition-colors"
              />
              <button
                v-if="rulesFilter"
                type="button"
                @click="rulesFilter = ''"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-fg-subtle/40 hover:text-fg-subtle transition-colors"
              >
                <X :size="11" />
              </button>
            </div>

            <div ref="rulesListRef" class="flex flex-col gap-1 max-h-48 overflow-y-auto pr-1">
              <div
                v-for="(rule, idx) in form.custom_rules"
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
                <div
                  v-show="!rulesFilter"
                  class="cursor-grab active:cursor-grabbing text-fg-subtle/20 hover:text-fg-subtle/50
                         transition-colors shrink-0 py-2 px-0.5 select-none"
                >
                  <GripVertical :size="12" />
                </div>

                <select
                  v-model="rule.type"
                  class="h-8 rounded-md border border-white/[0.08] bg-bg px-2 text-xs text-fg
                         focus:outline-none focus:border-white/20 transition-colors shrink-0"
                >
                  <option v-for="t in RULE_TYPES" :key="t" :value="t">{{ RULE_LABELS[t] }}</option>
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
                  :title="duplicateValues.has(rule.value.trim()) && rule.value.trim()
                    ? 'Дублирующееся значение'
                    : (submitAttempted && ruleError(rule) ? ruleError(rule) : undefined)"
                  @keydown.enter.prevent="addRule"
                />
                <button
                  type="button"
                  @click="removeRule(idx)"
                  class="p-1.5 rounded text-fg-subtle/40 hover:text-red-400 hover:bg-red-950/30 transition-colors shrink-0"
                >
                  <Trash2 :size="12" />
                </button>
              </div>

              <div v-if="rulesFilter && !hasVisibleRules"
                   class="py-3 text-center text-xs text-fg-subtle/40">
                Ничего не найдено
              </div>
            </div>
          </template>
        </div>

        <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <!-- footer -->
      <div class="flex items-center justify-end gap-2 px-6 py-4 shrink-0">
        <button
          @click="handleClose"
          class="h-8 px-4 rounded-md text-xs border border-white/[0.08] text-fg-subtle
                 hover:text-fg hover:border-white/20 transition-colors"
        >
          Отмена
        </button>
        <button
          @click="handleSubmit"
          :disabled="loading || !form.name.trim()"
          class="h-8 px-4 rounded-md text-xs font-medium text-[#1c1917] disabled:opacity-50 transition-opacity"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          {{ loading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </DialogContent>
  </Dialog>

  <UiConfirmDialog
    :open="closeConfirmOpen"
    variant="warning"
    title="Несохранённые изменения"
    description="Закрыть форму? Все изменения будут потеряны."
    confirm-text="Закрыть"
    cancel-text="Остаться"
    @update:open="v => !v && (closeConfirmOpen = false)"
    @confirm="confirmClose"
  />
</template>
