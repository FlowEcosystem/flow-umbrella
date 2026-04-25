<script setup>
import { X, Plus, Trash2, Zap, Check } from 'lucide-vue-next'
import { useServicesStore } from '@/domains/policies/servicesStore'

const props = defineProps({
  open:    { type: Boolean, required: true },
  target:  { type: Object,  default: null },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: '' },
})

const emit = defineEmits(['update:open', 'submit'])

const isEdit        = computed(() => !!props.target)
const servicesStore = useServicesStore()

// только сервисы с process-правилами
const processServices = computed(() =>
  servicesStore.items.filter(s => (s.rules ?? []).some(r => r.type === 'process'))
)

onMounted(() => { if (!servicesStore.items.length) servicesStore.fetch() })

const emptyForm = () => ({
  name:        '',
  description: '',
  action:      'block',
  is_active:   true,
  service_ids: [],
  processes:   [''],
})

const form            = ref(emptyForm())
const submitAttempted = ref(false)
const processListRef  = ref(null)
const presetOpen      = ref(false)

watch(() => props.open, v => {
  if (v) {
    if (props.target) {
      const procs = (props.target.custom_rules ?? [])
        .filter(r => r.type === 'process')
        .map(r => r.value)
      form.value = {
        name:        props.target.name,
        description: props.target.description ?? '',
        action:      props.target.action,
        is_active:   props.target.is_active,
        service_ids: (props.target.services ?? []).map(s => s.id),
        processes:   procs.length ? procs : [''],
      }
    } else {
      form.value = emptyForm()
    }
    submitAttempted.value = false
    presetOpen.value = false
  }
})

const filled = computed(() => form.value.processes.filter(p => p.trim()))

const hasRules = computed(() => filled.value.length > 0 || form.value.service_ids.length > 0)

const duplicates = computed(() => {
  const seen  = new Set()
  const dupes = new Set()
  for (const p of form.value.processes) {
    const v = p.trim().toLowerCase()
    if (!v) continue
    if (seen.has(v)) dupes.add(v)
    else seen.add(v)
  }
  return dupes
})

const addedServiceIds = computed(() => new Set(form.value.service_ids))

function toggleService(svc) {
  const id = svc.id
  if (addedServiceIds.value.has(id)) {
    form.value.service_ids = form.value.service_ids.filter(x => x !== id)
  } else {
    form.value.service_ids = [...form.value.service_ids, id]
  }
}

async function addProcess() {
  form.value.processes.push('')
  await nextTick()
  const inputs = processListRef.value?.querySelectorAll('input')
  inputs?.[inputs.length - 1]?.focus()
}

function removeProcess(idx) {
  form.value.processes.splice(idx, 1)
  if (!form.value.processes.length) form.value.processes.push('')
}

function handleSubmit() {
  submitAttempted.value = true
  if (!form.value.name.trim() || !hasRules.value) return
  emit('submit', {
    name:         form.value.name.trim(),
    description:  form.value.description.trim() || null,
    kind:         'process',
    action:       form.value.action,
    is_active:    form.value.is_active,
    service_ids:  form.value.service_ids,
    custom_rules: filled.value.map(p => ({ type: 'process', value: p.trim() })),
  })
}
</script>

<template>
  <Dialog :open="open" @update:open="v => !v && emit('update:open', false)">
    <DialogContent
      :show-close-button="false"
      class="max-w-[520px] p-0 border-white/[0.08] bg-bg-raised gap-0 flex flex-col max-h-[88vh]"
    >
      <!-- header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">
            {{ isEdit ? 'Редактировать политику' : 'Новая политика процессов' }}
          </DialogTitle>
          <DialogDescription class="text-xs text-fg-subtle mt-0.5">
            {{ isEdit ? target.name : 'Блокировать или разрешить запуск процессов на машине' }}
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
            placeholder="Игровые лаунчеры"
            class="h-9 w-full rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
            :class="submitAttempted && !form.name.trim() ? 'border-red-700/50' : ''"
          />
        </div>

        <!-- description -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">
            Описание <span class="text-fg-subtle/50">(необязательно)</span>
          </label>
          <textarea
            v-model="form.description"
            placeholder="Краткое описание"
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
                {{ a === 'block' ? 'Блокировать' : 'Разрешить' }}
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

        <!-- process services -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-xs text-fg-subtle">Группы процессов</label>
              <span v-if="form.service_ids.length"
                    class="text-[10px] text-fg-subtle/50 border border-white/[0.08] rounded px-1.5 py-0.5 tabular-nums">
                {{ form.service_ids.length }}
              </span>
            </div>
            <button
              v-if="processServices.length"
              type="button"
              @click="presetOpen = !presetOpen"
              class="flex items-center gap-1.5 h-7 px-2.5 rounded-md text-xs border transition-all duration-150"
              :class="presetOpen
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
            >
              <Zap :size="11" />
              Выбрать
            </button>
          </div>

          <!-- selected chips -->
          <div v-if="form.service_ids.length && !presetOpen" class="flex flex-wrap gap-1.5">
            <span
              v-for="id in form.service_ids" :key="id"
              class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border
                     border-accent/30 bg-accent/10 text-accent"
            >
              {{ servicesStore.items.find(s => s.id === id)?.name ?? id }}
              <button type="button"
                      @click="form.service_ids = form.service_ids.filter(x => x !== id)"
                      class="ml-0.5 opacity-60 hover:opacity-100 transition-opacity">
                <X :size="10" />
              </button>
            </span>
          </div>

          <!-- preset panel -->
          <Transition
            enter-active-class="transition-all duration-150 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            leave-active-class="transition-all duration-100 ease-in"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <div v-if="presetOpen"
                 class="rounded-xl border border-white/[0.08] bg-bg p-2 flex flex-col gap-1 max-h-40 overflow-y-auto">
              <button
                v-for="svc in processServices"
                :key="svc.id"
                type="button"
                @click="toggleService(svc)"
                class="flex items-center gap-2 h-8 px-2.5 rounded-md text-xs border transition-all duration-150 text-left"
                :class="addedServiceIds.has(svc.id)
                  ? 'border-accent/40 bg-accent/10 text-accent'
                  : 'border-white/[0.06] text-fg-subtle hover:text-fg hover:border-white/[0.12] hover:bg-white/[0.03]'"
              >
                <Check v-if="addedServiceIds.has(svc.id)" :size="11" class="shrink-0" />
                <span v-else class="w-[11px] shrink-0" />
                <span class="truncate flex-1">{{ svc.name }}</span>
                <span class="text-[10px] opacity-50 tabular-nums shrink-0">
                  {{ svc.rules.filter(r => r.type === 'process').length }} проц.
                </span>
              </button>
            </div>
          </Transition>

          <!-- hint when no process services exist -->
          <p v-if="!processServices.length" class="text-xs text-fg-subtle/40">
            Нет групп — создайте сервис с правилами типа «Процесс» во вкладке Сервисы
          </p>
        </div>

        <!-- custom process list -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-xs text-fg-subtle">Дополнительные процессы</label>
              <span v-if="filled.length"
                    class="text-[10px] text-fg-subtle/50 border border-white/[0.08] rounded px-1.5 py-0.5 tabular-nums">
                {{ filled.length }}
              </span>
            </div>
            <button type="button" @click="addProcess"
                    class="flex items-center gap-1 text-xs text-fg-subtle hover:text-fg transition-colors">
              <Plus :size="11" />
              Добавить
            </button>
          </div>

          <p v-if="submitAttempted && !hasRules" class="text-xs text-red-400">
            Добавьте хотя бы один процесс или группу
          </p>

          <div ref="processListRef" class="flex flex-col gap-1 max-h-48 overflow-y-auto pr-0.5">
            <div v-for="(_, idx) in form.processes" :key="idx"
                 class="flex items-center gap-1.5">
              <input
                v-model="form.processes[idx]"
                placeholder="javaw.exe"
                class="h-8 flex-1 rounded-md bg-bg px-3 text-xs text-fg font-mono border
                       placeholder:text-fg-subtle/40 focus:outline-none transition-colors"
                :class="duplicates.has(form.processes[idx].trim().toLowerCase()) && form.processes[idx].trim()
                  ? 'border-amber-700/50 focus:border-amber-600/60'
                  : 'border-white/[0.08] focus:border-white/20'"
                :title="duplicates.has(form.processes[idx].trim().toLowerCase()) && form.processes[idx].trim()
                  ? 'Дублирующееся значение' : undefined"
                @keydown.enter.prevent="addProcess"
              />
              <button
                type="button"
                @click="removeProcess(idx)"
                class="p-1.5 rounded text-fg-subtle/40 hover:text-red-400 hover:bg-red-950/30 transition-colors shrink-0"
              >
                <Trash2 :size="12" />
              </button>
            </div>
          </div>
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
          :disabled="loading"
          class="h-8 px-4 rounded-md text-xs font-medium text-[#1c1917] disabled:opacity-50 transition-opacity"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          {{ loading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>
