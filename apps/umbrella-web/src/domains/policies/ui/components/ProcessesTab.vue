<script setup>
import {
  RefreshCw, Search, ChevronDown, ChevronUp,
  ShieldOff, ShieldCheck, Copy, Loader2,
  Globe, Lock, Check, Trash2, X,
} from 'lucide-vue-next'
import { usePoliciesStore }       from '@/domains/policies/store'
import { usePagination }          from '@/shared/composables/usePagination'
import { usePermissions }         from '@/shared/composables/usePermissions'
import { useToast }               from '@/shared/composables/useToast'
import ProcessPolicyFormDialog    from '@/domains/policies/ui/components/ProcessPolicyFormDialog.vue'

const store        = usePoliciesStore()
const toast        = useToast()
const { canWrite } = usePermissions()

onMounted(() => { if (!store.items.length) store.fetch() })

const processPolicies = computed(() => store.items.filter(p => p.kind === 'process'))

const searchQuery = ref('')

const filtered = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return processPolicies.value
  return processPolicies.value.filter(p =>
    p.name.toLowerCase().includes(q) ||
    (p.description ?? '').toLowerCase().includes(q) ||
    (p.custom_rules ?? []).some(r => r.type === 'process' && r.value.toLowerCase().includes(q))
  )
})

// --- sorting ---
const sortBy  = ref(null)
const sortDir = ref('asc')

const SORT_COLS = [
  { key: 'name',   label: 'Название' },
  { key: 'action', label: 'Действие' },
]

function setSort(col) {
  if (sortBy.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = col
    sortDir.value = 'asc'
  }
}

const sortedFiltered = computed(() => {
  if (!sortBy.value) return filtered.value
  const col = sortBy.value
  return [...filtered.value].sort((a, b) => {
    let va = a[col]
    let vb = b[col]
    if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase() }
    if (va === vb) return 0
    const cmp = va > vb ? 1 : -1
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})

const { page, totalPages, paged: pagedPolicies, goTo } = usePagination(sortedFiltered, 24)

// --- bulk selection ---
const selectedIds    = ref([])
const hasSelection   = computed(() => selectedIds.value.length > 0)
const selectionCount = computed(() => selectedIds.value.length)

const allOnPageSelected = computed(() => {
  const local = pagedPolicies.value.filter(p => p.source === 'local')
  return local.length > 0 && local.every(p => selectedIds.value.includes(p.id))
})

function isSelected(id)  { return selectedIds.value.includes(id) }
function clearSelection() { selectedIds.value = [] }

function toggleSelect(id) {
  selectedIds.value = isSelected(id)
    ? selectedIds.value.filter(x => x !== id)
    : [...selectedIds.value, id]
}

function toggleSelectAll() {
  const localIds = pagedPolicies.value.filter(p => p.source === 'local').map(p => p.id)
  if (allOnPageSelected.value) {
    selectedIds.value = selectedIds.value.filter(id => !localIds.includes(id))
  } else {
    selectedIds.value = [...new Set([...selectedIds.value, ...localIds])]
  }
}

watch(filtered, (newList) => {
  const validIds = new Set(newList.map(p => p.id))
  selectedIds.value = selectedIds.value.filter(id => validIds.has(id))
})

// --- bulk operations ---
const bulkLoading    = ref(false)
const bulkDeleteOpen = ref(false)

async function bulkToggleActive(active) {
  const ids = [...selectedIds.value]
  ids.forEach(id => {
    const idx = store.items.findIndex(p => p.id === id)
    if (idx !== -1) store.items[idx].is_active = active
  })
  bulkLoading.value = true
  try {
    await Promise.all(ids.map(id => store.update(id, { is_active: active })))
    toast.success(`${ids.length} ${_policyWord(ids.length)} обновлено`)
    clearSelection()
  } catch {
    ids.forEach(id => {
      const idx = store.items.findIndex(p => p.id === id)
      if (idx !== -1) store.items[idx].is_active = !active
    })
    toast.error('Не удалось обновить статус')
  } finally {
    bulkLoading.value = false
  }
}

async function bulkDelete() {
  const ids = [...selectedIds.value]
  bulkDeleteOpen.value = false
  bulkLoading.value = true
  try {
    await Promise.all(ids.map(id => store.remove(id)))
    toast.success(`${ids.length} ${_policyWord(ids.length)} удалено`)
    clearSelection()
  } catch {
    toast.error('Не удалось удалить некоторые политики')
    await store.fetch()
  } finally {
    bulkLoading.value = false
  }
}

function _policyWord(n) {
  const m10 = n % 10, m100 = n % 100
  if (m100 >= 11 && m100 <= 19) return 'политик'
  if (m10 === 1) return 'политика'
  if (m10 >= 2 && m10 <= 4) return 'политики'
  return 'политик'
}

// --- expand ---
const expandedId = ref(null)
function toggleExpand(id) { expandedId.value = expandedId.value === id ? null : id }

// --- copy ---
const copiedVal = ref(null)
function copyVal(v) {
  navigator.clipboard.writeText(v)
  copiedVal.value = v
  setTimeout(() => { copiedVal.value = null }, 1500)
}

const ACTION_STYLES = {
  block: { badge: 'border-red-900/40 bg-red-950/50 text-red-400',            dot: 'bg-red-400' },
  allow: { badge: 'border-emerald-900/40 bg-emerald-950/50 text-emerald-400', dot: 'bg-emerald-400' },
}

// --- form ---
const formOpen    = ref(false)
const formTarget  = ref(null)
const formLoading = ref(false)
const formError   = ref('')

function openCreate() { formTarget.value = null; formError.value = ''; formOpen.value = true }
function openEdit(p)  { formTarget.value = p;    formError.value = ''; formOpen.value = true }

async function handleSubmit(data) {
  formLoading.value = true
  formError.value = ''
  try {
    if (formTarget.value) {
      await store.update(formTarget.value.id, data)
      toast.success('Политика обновлена')
    } else {
      await store.create(data)
      toast.success('Политика создана')
    }
    formOpen.value = false
  } catch (err) {
    formError.value = err.response?.data?.message ?? 'Ошибка сохранения'
  } finally {
    formLoading.value = false
  }
}

// --- toggle active ---
const toggleLoading = ref({})

async function toggleActive(policy) {
  const idx  = store.items.findIndex(p => p.id === policy.id)
  const prev = policy.is_active
  if (idx !== -1) store.items[idx].is_active = !prev
  toggleLoading.value[policy.id] = true
  try {
    await store.update(policy.id, { is_active: !prev })
  } catch {
    if (idx !== -1) store.items[idx].is_active = prev
    toast.error('Не удалось изменить статус')
  } finally {
    delete toggleLoading.value[policy.id]
  }
}

// --- delete ---
const deleteTarget  = ref(null)
const deleteLoading = ref(false)

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await store.remove(deleteTarget.value.id)
    toast.success('Политика удалена')
    deleteTarget.value = null
  } catch {
    toast.error('Не удалось удалить политику')
  } finally {
    deleteLoading.value = false
  }
}

defineExpose({ openCreate })

function processesSuffix(n) {
  const m10 = n % 10, m100 = n % 100
  if (m100 >= 11 && m100 <= 19) return 'процессов'
  if (m10 === 1) return 'процесс'
  if (m10 >= 2 && m10 <= 4) return 'процесса'
  return 'процессов'
}
</script>

<template>
  <div>

    <!-- skeleton -->
    <div v-if="store.isLoading && !store.items.length" class="flex flex-col gap-2">
      <div v-for="i in 4" :key="i"
           class="bg-bg-raised border border-white/[0.06] rounded-xl px-5 py-4 flex items-center gap-4">
        <div class="h-4 w-40 rounded bg-white/[0.05]" />
        <div class="h-5 w-20 rounded-md bg-white/[0.05]" />
        <div class="h-3 w-24 rounded bg-white/[0.04] ml-auto" />
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
    <div v-else-if="!store.isLoading && !processPolicies.length"
         class="flex flex-col items-center justify-center py-20 gap-3">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="1.3" class="text-fg-subtle/40">
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <path d="M8 21h8M12 17v4"/>
        <path d="m9 8 3 3 3-3"/>
      </svg>
      <p class="text-sm text-fg-subtle">Политик процессов пока нет</p>
      <button v-if="canWrite" @click="openCreate"
              class="text-xs text-accent hover:text-accent-lit transition-colors">
        Создать первую
      </button>
    </div>

    <!-- content -->
    <template v-else>

      <!-- toolbar -->
      <div class="flex items-center gap-2 mb-4">
        <div class="relative flex-1 min-w-0 max-w-sm">
          <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/50 pointer-events-none" />
          <input
            v-model="searchQuery"
            placeholder="Поиск по названию или процессу..."
            class="h-8 w-full rounded-md border bg-bg-raised pl-9 pr-3 text-xs text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none transition-colors"
            :class="searchQuery ? 'border-accent/40' : 'border-white/[0.08] focus:border-white/20'"
          />
        </div>
        <span v-if="processPolicies.length" class="text-xs text-fg-subtle/50 tabular-nums ml-1">
          {{ searchQuery ? `${filtered.length} из ${processPolicies.length}` : processPolicies.length }}
        </span>
        <button
          @click="store.fetch()" :disabled="store.isLoading"
          class="h-8 w-8 ml-auto flex items-center justify-center rounded-md border border-white/[0.08]
                 text-fg-subtle hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
        >
          <RefreshCw :size="12" :class="store.isLoading ? 'animate-spin' : ''" />
        </button>
      </div>

      <!-- sort + select-all bar -->
      <div v-if="filtered.length > 1" class="flex items-center gap-2 mb-3">
        <button
          v-if="canWrite"
          type="button"
          @click="toggleSelectAll"
          class="w-4 h-4 rounded flex items-center justify-center border transition-all shrink-0"
          :class="allOnPageSelected
            ? 'border-accent bg-accent/20 text-accent'
            : hasSelection
              ? 'border-accent/40 bg-accent/10 text-accent/60'
              : 'border-white/[0.12] text-transparent hover:border-white/30'"
          title="Выбрать всё на странице"
        >
          <Check :size="10" />
        </button>
        <span class="text-xs text-fg-subtle/60 uppercase tracking-wider">Сортировка</span>
        <div class="flex gap-1">
          <button
            v-for="col in SORT_COLS" :key="col.key"
            @click="setSort(col.key)"
            class="flex items-center gap-1 h-6 px-2 rounded text-xs border transition-all duration-150"
            :class="sortBy === col.key
              ? 'border-accent/40 bg-accent/10 text-accent'
              : 'border-white/[0.06] text-fg-subtle/50 hover:text-fg hover:border-white/[0.12]'"
          >
            {{ col.label }}
            <ChevronUp
              v-if="sortBy === col.key"
              :size="10"
              class="transition-transform duration-150"
              :class="sortDir === 'desc' ? 'rotate-180' : ''"
            />
          </button>
        </div>
      </div>

      <!-- no search results -->
      <div v-if="!filtered.length" class="flex flex-col items-center justify-center py-16 gap-2">
        <p class="text-sm text-fg-subtle">Ничего не найдено</p>
        <button @click="searchQuery = ''" class="text-xs text-accent hover:text-accent-lit transition-colors">
          Сбросить поиск
        </button>
      </div>

      <!-- list -->
      <div v-else class="flex flex-col gap-1.5">
        <div
          v-for="policy in pagedPolicies"
          :key="policy.id"
          class="group bg-bg-raised border rounded-xl overflow-hidden transition-colors duration-200"
          :class="expandedId === policy.id ? 'border-white/[0.12]' : 'border-white/[0.06] hover:border-white/[0.10]'"
        >
          <!-- row -->
          <div class="flex items-center gap-3 px-4 py-3 cursor-pointer select-none"
               @click="toggleExpand(policy.id)">

            <!-- checkbox -->
            <div class="shrink-0 w-4 h-4 flex items-center justify-center" @click.stop>
              <button
                v-if="canWrite && policy.source === 'local'"
                type="button"
                @click="toggleSelect(policy.id)"
                class="w-4 h-4 rounded flex items-center justify-center border transition-all"
                :class="[
                  isSelected(policy.id)
                    ? 'border-accent bg-accent/20 text-accent'
                    : 'border-white/[0.16] text-transparent hover:border-white/40',
                  hasSelection ? 'opacity-100' : 'opacity-0 group-hover:opacity-100',
                ]"
              >
                <Check :size="10" />
              </button>
            </div>

            <!-- source icon -->
            <div class="shrink-0 text-fg-subtle/40">
              <Globe v-if="policy.source === 'global'" :size="14" class="text-blue-400/60" />
              <Lock v-else :size="14" />
            </div>

            <!-- name -->
            <div class="flex-1 min-w-0">
              <span class="text-sm font-medium truncate transition-colors"
                    :class="policy.is_active ? 'text-fg' : 'text-fg-subtle/60'">
                {{ policy.name }}
              </span>
              <p v-if="policy.description" class="text-xs text-fg-subtle/50 truncate mt-0.5">
                {{ policy.description }}
              </p>
            </div>

            <!-- action badge -->
            <span class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded border shrink-0"
                  :class="ACTION_STYLES[policy.action].badge">
              <ShieldOff v-if="policy.action === 'block'" :size="10" />
              <ShieldCheck v-else :size="10" />
              {{ policy.action === 'block' ? 'Блокировать' : 'Разрешить' }}
            </span>

            <!-- process count -->
            <span class="text-xs text-fg-subtle/50 tabular-nums shrink-0">
              {{
                (policy.custom_rules ?? []).filter(r => r.type === 'process').length
              }} {{ processesSuffix((policy.custom_rules ?? []).filter(r => r.type === 'process').length) }}
            </span>

            <!-- actions (local only) -->
            <div v-if="canWrite && policy.source === 'local'"
                 class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                 @click.stop>

              <button
                @click="toggleActive(policy)"
                :disabled="!!toggleLoading[policy.id]"
                class="relative w-8 h-[18px] rounded-full border transition-all duration-200 disabled:opacity-50"
                :class="policy.is_active
                  ? 'bg-accent/20 border-accent/50'
                  : 'bg-white/[0.04] border-white/[0.12]'"
                :title="policy.is_active ? 'Деактивировать' : 'Активировать'"
              >
                <Loader2 v-if="toggleLoading[policy.id]" :size="10"
                         class="absolute inset-0 m-auto animate-spin text-fg-subtle" />
                <span v-else
                      class="absolute top-[2px] w-[13px] h-[13px] rounded-full transition-all duration-200"
                      :class="policy.is_active ? 'left-[18px] bg-accent' : 'left-[2px] bg-fg-subtle/40'" />
              </button>

              <button @click="openEdit(policy)"
                      class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors"
                      title="Редактировать">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button @click="deleteTarget = policy"
                      class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30 transition-colors"
                      title="Удалить">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14H6L5 6"/>
                  <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
                </svg>
              </button>
            </div>

            <span v-else-if="policy.source === 'global'"
                  class="text-xs text-fg-subtle/50 opacity-0 group-hover:opacity-100 transition-opacity">
              только чтение
            </span>

            <ChevronDown :size="14"
                         class="shrink-0 text-fg-subtle/40 transition-transform duration-200 ml-1"
                         :class="expandedId === policy.id ? 'rotate-180 text-fg-subtle/60' : ''" />
          </div>

          <!-- expanded processes -->
          <Transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            leave-active-class="transition-all duration-150 ease-in"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <div v-if="expandedId === policy.id"
                 class="border-t border-white/[0.06] px-4 py-3 bg-bg/40">
              <div v-if="!(policy.custom_rules ?? []).filter(r => r.type === 'process').length"
                   class="text-xs text-fg-subtle/40 text-center py-2">
                Нет процессов
              </div>
              <div v-else class="flex flex-wrap gap-1.5">
                <span
                  v-for="rule in (policy.custom_rules ?? []).filter(r => r.type === 'process')"
                  :key="rule.value"
                  @click.stop="copyVal(rule.value)"
                  class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border font-mono
                         cursor-pointer select-none transition-all duration-150
                         border-orange-900/40 bg-orange-950/30 text-orange-300/80"
                  :class="copiedVal === rule.value ? 'opacity-40 scale-95' : 'hover:brightness-125'"
                  title="Копировать"
                >
                  <Copy v-if="copiedVal !== rule.value" :size="10" class="text-orange-400/50" />
                  {{ rule.value }}
                </span>
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <UiPagination :page="page" :total-pages="totalPages" @go="goTo" />

    </template>

    <ProcessPolicyFormDialog
      v-model:open="formOpen"
      :target="formTarget"
      :loading="formLoading"
      :error="formError"
      @submit="handleSubmit"
    />

    <UiConfirmDialog
      :open="!!deleteTarget"
      variant="danger"
      title="Удаление политики"
      :description="`Удалить политику «${deleteTarget?.name}»?`"
      confirm-text="Удалить"
      :loading="deleteLoading"
      @update:open="v => !v && (deleteTarget = null)"
      @confirm="confirmDelete"
    />

    <UiConfirmDialog
      :open="bulkDeleteOpen"
      variant="danger"
      title="Массовое удаление"
      :description="`Удалить ${selectionCount} политик? Это действие необратимо.`"
      confirm-text="Удалить"
      :loading="bulkLoading"
      @update:open="v => !v && (bulkDeleteOpen = false)"
      @confirm="bulkDelete"
    />

    <!-- bulk action bar -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      leave-active-class="transition-all duration-150 ease-in"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="hasSelection"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-1.5 px-3 py-2 rounded-xl
               border border-white/[0.12] bg-bg-raised shadow-2xl"
      >
        <span class="text-xs text-fg-subtle px-1.5 tabular-nums flex items-center gap-1.5">
          <Loader2 v-if="bulkLoading" :size="11" class="animate-spin opacity-60" />
          {{ selectionCount }} выбрано
        </span>
        <div class="w-px h-4 bg-white/[0.08] mx-0.5" />

        <button
          @click="bulkToggleActive(true)"
          :disabled="bulkLoading"
          class="h-7 px-2.5 rounded-md text-xs border border-emerald-800/40 bg-emerald-950/30 text-emerald-400
                 hover:bg-emerald-950/50 transition-colors disabled:opacity-40"
        >
          Активировать
        </button>
        <button
          @click="bulkToggleActive(false)"
          :disabled="bulkLoading"
          class="h-7 px-2.5 rounded-md text-xs border border-white/[0.08] text-fg-subtle
                 hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
        >
          Деактивировать
        </button>

        <div class="w-px h-4 bg-white/[0.08] mx-0.5" />

        <button
          @click="bulkDeleteOpen = true"
          :disabled="bulkLoading"
          class="h-7 px-2.5 rounded-md text-xs border border-red-900/40 bg-red-950/30 text-red-400
                 hover:bg-red-950/50 transition-colors disabled:opacity-40"
        >
          <Trash2 :size="11" class="inline -mt-px mr-1" />
          Удалить
        </button>

        <div class="w-px h-4 bg-white/[0.08] mx-0.5" />

        <button
          @click="clearSelection"
          class="p-1.5 rounded text-fg-subtle/50 hover:text-fg transition-colors"
          title="Снять выделение (Esc)"
        >
          <X :size="12" />
        </button>
      </div>
    </Transition>
  </div>
</template>
