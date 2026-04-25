<script setup>
import { RefreshCw, Search, ChevronDown, Upload, Download } from 'lucide-vue-next'
import { useServicesStore } from '@/domains/policies/servicesStore'
import { usePermissions }   from '@/shared/composables/usePermissions'
import { useToast }         from '@/shared/composables/useToast'
import ServiceFormDialog    from '@/domains/policies/ui/components/ServiceFormDialog.vue'
import CsvImportDialog      from '@/domains/policies/ui/components/CsvImportDialog.vue'

const store        = useServicesStore()
const toast        = useToast()
const { canWrite } = usePermissions()

onMounted(() => { if (!store.items.length) store.fetch() })

const KINDS = [
  { key: 'traffic', label: 'Трафик',   hint: 'Домены, URL, IP-адреса' },
  { key: 'process', label: 'Процессы', hint: 'Исполняемые файлы' },
]

const activeKind = ref('traffic')

const kindCounts = computed(() => ({
  traffic: store.items.filter(s => (s.kind ?? 'traffic') === 'traffic').length,
  process: store.items.filter(s => s.kind === 'process').length,
}))

watch(activeKind, () => {
  selectedCategory.value = null
  searchQuery.value = ''
  expandedId.value = null
})

const kindItems = computed(() => store.items.filter(s => (s.kind ?? 'traffic') === activeKind.value))

const kindGrouped = computed(() => {
  const map = new Map()
  for (const s of kindItems.value) {
    if (!map.has(s.category)) map.set(s.category, [])
    map.get(s.category).push(s)
  }
  return [...map.entries()].map(([label, services]) => ({ label, services }))
})

// --- category sidebar ---
const selectedCategory = ref(null)

watch(kindGrouped, (groups) => {
  if (groups.length && !selectedCategory.value) selectedCategory.value = groups[0].label
}, { immediate: true })

// --- search within selected category ---
const searchQuery = ref('')

watch(selectedCategory, () => {
  expandedId.value = null
  searchQuery.value = ''
})

const currentServices = computed(() => {
  const group = kindGrouped.value.find(g => g.label === selectedCategory.value)
  const services = group?.services ?? []
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return services
  return services.filter(s => s.name.toLowerCase().includes(q))
})

// --- expand ---
const expandedId = ref(null)
function toggleExpand(id) { expandedId.value = expandedId.value === id ? null : id }

const RULE_TYPE_STYLES = {
  domain:  'border-white/[0.08] text-fg-subtle/60',
  url:     'border-violet-800/40 text-violet-400/70',
  ip:      'border-cyan-800/40 text-cyan-400/70',
  process: 'border-orange-900/40 text-orange-300/80',
}

// --- copy ---
const copiedRule = ref(null)
function copyRule(value) {
  navigator.clipboard.writeText(value)
  copiedRule.value = value
  setTimeout(() => { copiedRule.value = null }, 1500)
}

// --- form ---
const formOpen    = ref(false)
const formTarget  = ref(null)
const formLoading = ref(false)
const formError   = ref('')

function openCreate() { formTarget.value = null; formError.value = ''; formOpen.value = true }
function openEdit(svc) { formTarget.value = svc; formError.value = ''; formOpen.value = true }

async function handleSubmit(data) {
  formLoading.value = true
  formError.value = ''
  try {
    if (formTarget.value) {
      await store.update(formTarget.value.id, data)
      toast.success('Сервис обновлён')
    } else {
      await store.create({ ...data, kind: activeKind.value })
      selectedCategory.value = data.category
      toast.success('Сервис создан')
    }
    formOpen.value = false
  } catch (err) {
    formError.value = err.response?.data?.message ?? 'Ошибка сохранения'
  } finally {
    formLoading.value = false
  }
}

// --- delete ---
const deleteTarget  = ref(null)
const deleteLoading = ref(false)

function openDelete(svc) { deleteTarget.value = svc }

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await store.remove(deleteTarget.value.id)
    toast.success('Сервис удалён')
    deleteTarget.value = null
  } catch {
    toast.error('Не удалось удалить сервис')
  } finally {
    deleteLoading.value = false
  }
}

const csvImportOpen = ref(false)

function exportCsv() {
  const rows = [['name', 'category', 'rule_type', 'rule_value']]
  for (const svc of kindItems.value) {
    if (!svc.rules?.length) {
      rows.push([svc.name, svc.category, '', ''])
    } else {
      for (const rule of svc.rules) {
        rows.push([svc.name, svc.category, rule.type, rule.value])
      }
    }
  }
  const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url
  a.download = 'services.csv'
  a.click()
  URL.revokeObjectURL(url)
}

defineExpose({ openCreate })

function rulesSuffix(n) {
  const m10 = n % 10, m100 = n % 100
  if (m100 >= 11 && m100 <= 19) return 'правил'
  if (m10 === 1) return 'правило'
  if (m10 >= 2 && m10 <= 4) return 'правила'
  return 'правил'
}
</script>

<template>
  <div>

    <!-- kind switcher -->
    <div class="flex items-center gap-2 mb-5">
      <div class="flex gap-1 p-1 rounded-lg border border-white/[0.08] bg-bg-raised">
        <button
          v-for="k in KINDS"
          :key="k.key"
          @click="activeKind = k.key"
          class="flex items-center gap-1.5 h-7 px-3 rounded-md text-xs transition-all duration-150"
          :class="activeKind === k.key
            ? 'bg-white/[0.08] text-fg'
            : 'text-fg-subtle hover:text-fg'"
        >
          {{ k.label }}
          <span
            class="tabular-nums text-[10px]"
            :class="activeKind === k.key ? 'text-fg-subtle/60' : 'text-fg-subtle/35'"
          >{{ kindCounts[k.key] }}</span>
        </button>
      </div>
      <span class="text-xs text-fg-subtle/40">
        {{ KINDS.find(k => k.key === activeKind)?.hint }}
      </span>
    </div>

    <!-- loading skeleton -->
    <div v-if="store.isLoading && !store.items.length" class="flex gap-5">
      <div class="w-48 shrink-0 flex flex-col gap-1">
        <div v-for="i in 7" :key="i" class="h-8 rounded-lg bg-white/[0.04]" />
      </div>
      <div class="flex-1 flex flex-col gap-2">
        <div v-for="i in 5" :key="i"
             class="bg-bg-raised border border-white/[0.06] rounded-xl px-5 py-4 flex items-center gap-4">
          <div class="h-4 w-32 rounded bg-white/[0.05]" />
          <div class="h-5 w-20 rounded-md bg-white/[0.05]" />
          <div class="h-3 w-16 rounded bg-white/[0.04] ml-auto" />
        </div>
      </div>
    </div>

    <!-- error -->
    <div v-else-if="store.error" class="flex flex-col items-center gap-3 py-16 text-center">
      <p class="text-sm text-red-400">{{ store.error }}</p>
      <button @click="store.fetch()" class="text-xs text-fg-subtle hover:text-fg transition-colors underline">
        Попробовать снова
      </button>
    </div>

    <!-- empty -->
    <div v-else-if="!store.isLoading && !kindGrouped.length"
         class="flex flex-col items-center justify-center py-20 gap-3">
      <p class="text-sm text-fg-subtle">Сервисов пока нет</p>
      <button v-if="canWrite" @click="openCreate"
              class="text-xs text-accent hover:text-accent-lit transition-colors">
        Создать первый сервис
      </button>
    </div>

    <!-- two-column layout -->
    <div v-else class="flex gap-5">

      <!-- LEFT: category nav -->
      <div class="w-48 shrink-0 flex flex-col gap-0.5">
        <p class="text-xs uppercase tracking-wider text-fg-subtle/60 px-3 mb-2 select-none">
          Категории
        </p>
        <button
          v-for="group in kindGrouped"
          :key="group.label"
          @click="selectedCategory = group.label"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm text-left transition-colors duration-150"
          :class="selectedCategory === group.label
            ? 'bg-white/[0.08] text-fg'
            : 'text-fg-subtle hover:text-fg hover:bg-white/[0.04]'"
        >
          <span class="truncate">{{ group.label }}</span>
          <span class="text-xs tabular-nums shrink-0 ml-2"
                :class="selectedCategory === group.label ? 'text-fg-subtle/70' : 'text-fg-subtle/40'">
            {{ group.services.length }}
          </span>
        </button>
      </div>

      <!-- RIGHT: service list -->
      <div class="flex-1 min-w-0">

        <!-- toolbar -->
        <div class="flex items-center gap-2 mb-4">
          <div class="relative flex-1 min-w-0">
            <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/50 pointer-events-none" />
            <input
              v-model="searchQuery"
              placeholder="Поиск в категории..."
              class="h-8 w-full rounded-md border bg-bg-raised pl-9 pr-3 text-xs text-fg
                     placeholder:text-fg-subtle/40 focus:outline-none transition-colors"
              :class="searchQuery ? 'border-accent/40' : 'border-white/[0.08] focus:border-white/20'"
            />
          </div>
          <button
            v-if="store.items.length"
            @click="exportCsv"
            class="h-8 px-3 flex items-center gap-1.5 rounded-md border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors shrink-0 text-xs"
            title="Экспорт в CSV"
          >
            <Download :size="12" />
            Экспорт
          </button>
          <button
            v-if="canWrite"
            @click="csvImportOpen = true"
            class="h-8 px-3 flex items-center gap-1.5 rounded-md border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors shrink-0 text-xs"
            title="Импорт из CSV"
          >
            <Upload :size="12" />
            Импорт
          </button>
          <button
            @click="store.fetch()" :disabled="store.isLoading"
            class="h-8 w-8 flex items-center justify-center rounded-md border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40 shrink-0"
          >
            <RefreshCw :size="12" :class="store.isLoading ? 'animate-spin' : ''" />
          </button>
        </div>

        <!-- no results -->
        <div v-if="!currentServices.length"
             class="flex flex-col items-center justify-center py-16 gap-2">
          <p class="text-sm text-fg-subtle">
            {{ searchQuery ? 'Ничего не найдено' : 'Нет сервисов в категории' }}
          </p>
          <button v-if="searchQuery" @click="searchQuery = ''"
                  class="text-xs text-accent hover:text-accent-lit transition-colors">
            Сбросить поиск
          </button>
        </div>

        <!-- service rows -->
        <div v-else class="flex flex-col gap-1.5">
          <div
            v-for="svc in currentServices"
            :key="svc.id"
            class="group bg-bg-raised border rounded-xl overflow-hidden transition-colors duration-200"
            :class="expandedId === svc.id ? 'border-white/[0.12]' : 'border-white/[0.06] hover:border-white/[0.10]'"
          >
            <!-- row -->
            <div class="flex items-center gap-3 px-4 py-3 cursor-pointer select-none"
                 @click="toggleExpand(svc.id)">
              <span class="text-sm font-medium text-fg flex-1 min-w-0 truncate">{{ svc.name }}</span>

              <span v-if="svc.source === 'global'"
                    class="text-[11px] px-1.5 py-0.5 rounded border border-blue-800/40 bg-blue-950/50 text-blue-400 shrink-0">
                global
              </span>

              <span class="text-xs text-fg-subtle/50 tabular-nums shrink-0">
                {{ svc.rules_count }} {{ rulesSuffix(svc.rules_count) }}
              </span>

              <div v-if="canWrite && svc.source === 'local'"
                   class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                   @click.stop>
                <button @click="openEdit(svc)"
                        class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors"
                        title="Редактировать">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button @click="openDelete(svc)"
                        class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30 transition-colors"
                        title="Удалить">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14H6L5 6"/>
                    <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
                  </svg>
                </button>
              </div>

              <ChevronDown :size="14"
                           class="shrink-0 text-fg-subtle/40 transition-transform duration-200 ml-1"
                           :class="expandedId === svc.id ? 'rotate-180 text-fg-subtle/60' : ''" />
            </div>

            <!-- expanded rules -->
            <Transition
              enter-active-class="transition-all duration-200 ease-out"
              enter-from-class="opacity-0 -translate-y-1"
              leave-active-class="transition-all duration-150 ease-in"
              leave-to-class="opacity-0 -translate-y-1"
            >
              <div v-if="expandedId === svc.id"
                   class="border-t border-white/[0.06] px-4 py-3 bg-bg/40">
                <div v-if="!svc.rules.length" class="text-xs text-fg-subtle/40 text-center py-2">
                  Нет правил
                </div>
                <div v-else class="flex flex-col gap-2">
                  <template v-for="type in ['domain', 'url', 'ip', 'process']" :key="type">
                    <div v-if="svc.rules.filter(r => r.type === type).length">
                      <p class="text-xs uppercase tracking-wide text-fg-subtle/60 mb-1 select-none">
                        {{ { domain: 'Домены', url: 'URL', ip: 'IP / CIDR', process: 'Процессы' }[type] }}
                      </p>
                      <div class="flex flex-wrap gap-1">
                        <span
                          v-for="rule in svc.rules.filter(r => r.type === type)"
                          :key="rule.value"
                          @click.stop="copyRule(rule.value)"
                          class="inline-flex items-center text-xs px-2 py-0.5 rounded border font-mono
                                 cursor-pointer select-none transition-all duration-150"
                          :class="[RULE_TYPE_STYLES[type], copiedRule === rule.value ? 'opacity-40 scale-95' : 'hover:brightness-125']"
                          title="Копировать"
                        >
                          {{ rule.value }}
                        </span>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>

    <CsvImportDialog v-model:open="csvImportOpen" />

    <ServiceFormDialog
      v-model:open="formOpen"
      :target="formTarget"
      :kind="activeKind"
      :loading="formLoading"
      :error="formError"
      @submit="handleSubmit"
    />

    <UiConfirmDialog
      :open="!!deleteTarget"
      variant="danger"
      title="Удаление сервиса"
      :description="`Удалить сервис «${deleteTarget?.name}»? Политики, использующие его, потеряют эти правила.`"
      confirm-text="Удалить"
      :loading="deleteLoading"
      @update:open="v => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />
  </div>
</template>
