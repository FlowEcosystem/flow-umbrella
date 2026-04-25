<script setup>
import {
  Plus, Search, ShieldCheck, RefreshCw, X,
  ShieldOff, Globe, Lock, ChevronDown, Copy, Loader2,
  Check, ChevronUp, Trash2, Target,
} from 'lucide-vue-next'
import { usePoliciesPage, SORT_COLS } from '@/domains/policies/usePoliciesPage'
import { usePermissions }             from '@/shared/composables/usePermissions'
import { useServicesStore }           from '@/domains/policies/servicesStore'
import PolicyFormDialog               from '@/domains/policies/ui/components/PolicyFormDialog.vue'
import PolicyAssignDialog             from '@/domains/policies/ui/components/PolicyAssignDialog.vue'
import ServicesTab                    from '@/domains/policies/ui/components/ServicesTab.vue'
import ProcessesTab                   from '@/domains/policies/ui/components/ProcessesTab.vue'
import PolicyTestDialog               from '@/domains/policies/ui/components/PolicyTestDialog.vue'

const route  = useRoute()
const router = useRouter()

const TABS = [
  { key: 'policies',  label: 'Трафик'   },
  { key: 'processes', label: 'Процессы' },
  { key: 'services',  label: 'Сервисы'  },
]

const activeTab = computed({
  get: () => {
    const t = route.query.tab
    return TABS.some(x => x.key === t) ? t : 'policies'
  },
  set: (v) => router.replace({ query: v !== 'policies' ? { tab: v } : {} }),
})

const servicesTabRef  = ref(null)
const processesTabRef = ref(null)
const testOpen        = ref(false)

function handleCreateClick() {
  if (activeTab.value === 'services')  servicesTabRef.value?.openCreate()
  else if (activeTab.value === 'processes') processesTabRef.value?.openCreate()
  else openCreate()
}

const {
  store,
  filteredPolicies, pagedPolicies, page, totalPages, goTo,
  searchQuery, activeAction, activeSource, hasFilters,
  setAction, setSource, resetFilters,
  sortBy, sortDir, setSort,
  selectedIds, hasSelection, selectionCount, allOnPageSelected,
  isSelected, toggleSelect, toggleSelectAll, clearSelection,
  bulkLoading, bulkDeleteOpen, bulkToggleActive, bulkDuplicate, bulkDelete,
  formOpen, formTarget, formData, formLoading, formError, flashId,
  openCreate, openEdit, submitForm,
  toggleLoading, toggleActive,
  expandedId, toggleExpand,
  duplicateLoading, duplicatePolicy,
  deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
  ACTION_LABELS, SOURCE_LABELS, RULE_LABELS, POLICY_ACTIONS, POLICY_SOURCES,
} = usePoliciesPage()

const { canWrite } = usePermissions()

const servicesStore = useServicesStore()

const tabCounts = computed(() => ({
  policies:  store.items.filter(p => (p.kind ?? 'traffic') !== 'process').length,
  processes: store.items.filter(p => p.kind === 'process').length,
  services:  servicesStore.items.length,
}))

const activeCount = computed(() => store.items.filter(p => p.is_active).length)

function onKeydown(e) {
  const tag = e.target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  if (formOpen.value || !!deleteTarget.value || bulkDeleteOpen.value) return

  if (e.key === 'n' || e.key === 'N') {
    if (canWrite.value) { e.preventDefault(); handleCreateClick() }
    return
  }
  if (e.key === 'Escape') {
    if (hasSelection.value) { clearSelection(); return }
    if (expandedId.value !== null) { expandedId.value = null; return }
    if (hasFilters.value) resetFilters()
    return
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const ids = pagedPolicies.value.map(p => p.id)
    if (!expandedId.value) { expandedId.value = ids[0] ?? null; return }
    const i = ids.indexOf(expandedId.value)
    if (i < ids.length - 1) expandedId.value = ids[i + 1]
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    const ids = pagedPolicies.value.map(p => p.id)
    if (!expandedId.value) return
    const i = ids.indexOf(expandedId.value)
    expandedId.value = i > 0 ? ids[i - 1] : null
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

const ACTION_STYLES = {
  block: { badge: 'border-red-900/40 bg-red-950/50 text-red-400',           dot: 'bg-red-400' },
  allow: { badge: 'border-emerald-900/40 bg-emerald-950/50 text-emerald-400', dot: 'bg-emerald-400' },
}
const SOURCE_STYLES = {
  local:  'border-accent/30 bg-accent/10 text-accent',
  global: 'border-blue-800/40 bg-blue-950/50 text-blue-400',
}
const RULE_TYPE_STYLES = {
  domain:  'border-white/[0.08] text-fg-subtle/60',
  url:     'border-violet-800/40 text-violet-400/70',
  ip:      'border-cyan-800/40 text-cyan-400/70',
  process: 'border-orange-900/40 text-orange-300/80',
}

function rulesSuffix(n) {
  const m10 = n % 10, m100 = n % 100
  if (m100 >= 11 && m100 <= 19) return 'правил'
  if (m10 === 1) return 'правило'
  if (m10 >= 2 && m10 <= 4) return 'правила'
  return 'правил'
}

// --- copy rule chip ---
const copiedRule = ref(null)
function copyRule(value) {
  navigator.clipboard.writeText(value)
  copiedRule.value = value
  setTimeout(() => { copiedRule.value = null }, 1500)
}

// --- expanded row: custom rules panel ---
const GROUP_PREVIEW  = 6
const expandedGroups = ref({})
const rulesSearch    = ref({})

function setRulesSearch(policyId, q) {
  const next = { ...rulesSearch.value }
  if (q) next[policyId] = q
  else delete next[policyId]
  rulesSearch.value = next
}

watch(expandedId, (_, oldId) => {
  if (oldId) setRulesSearch(oldId, '')
})

function groupedCustomRules(policy) {
  const q = (rulesSearch.value[policy.id] ?? '').trim().toLowerCase()
  return ['domain', 'url', 'ip', 'process']
    .map(type => {
      const all     = (policy.custom_rules ?? []).filter(r => r.type === type)
      const matched = q ? all.filter(r => r.value.toLowerCase().includes(q)) : all
      const key     = `${policy.id}:${type}`
      const shown   = (q || expandedGroups.value[key]) ? matched : matched.slice(0, GROUP_PREVIEW)
      return { type, shown, total: all.length, matchedCount: matched.length, searching: !!q }
    })
    .filter(g => g.searching ? g.matchedCount > 0 : g.total > 0)
}

function toggleGroup(policyId, type) {
  const key  = `${policyId}:${type}`
  const next = { ...expandedGroups.value }
  if (next[key]) delete next[key]
  else next[key] = true
  expandedGroups.value = next
}

// --- assign dialog ---
const assignTarget = ref(null)
function openAssign(policy) { assignTarget.value = policy }

// --- delete row animation ---
function onLeave(el) {
  const h = el.offsetHeight
  el.style.height   = h + 'px'
  el.style.overflow = 'hidden'
  requestAnimationFrame(() => {
    el.style.transition = 'height 0.2s ease, opacity 0.15s ease, margin-bottom 0.2s ease'
    el.style.height      = '0'
    el.style.opacity     = '0'
    el.style.marginBottom = '-8px'
  })
}
</script>

<template>
  <div>
    <div class="px-8 py-8 max-w-6xl mx-auto w-full">

      <!-- header -->
      <div class="flex items-start justify-between mb-7">
        <div>
          <h1 class="text-4xl text-fg mb-1.5 leading-tight font-serif font-normal">Политики</h1>
          <p class="text-sm text-fg-subtle">Правила фильтрации трафика и контроля доступа.</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            v-if="activeTab !== 'services'"
            @click="testOpen = true"
            class="flex items-center gap-2 h-9 px-4 rounded-lg text-sm border border-white/[0.10]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              <path d="M11 8v6M8 11h6"/>
            </svg>
            Тест
          </button>
          <!-- tab switcher -->
          <div class="flex items-center gap-0.5 border border-white/[0.08] rounded-lg p-1 bg-bg-raised">
            <template v-for="tab in TABS" :key="tab.key">
              <div v-if="tab.key === 'services'" class="w-px h-4 bg-white/[0.10] mx-0.5 shrink-0" />
              <button
                @click="activeTab = tab.key"
                class="h-7 px-3 rounded-md text-xs transition-all duration-150 flex items-center gap-1.5"
                :class="activeTab === tab.key
                  ? 'bg-white/[0.08] text-fg'
                  : 'text-fg-subtle hover:text-fg'"
              >
                {{ tab.label }}
                <span
                  v-if="tabCounts[tab.key]"
                  class="tabular-nums text-[10px] leading-none"
                  :class="activeTab === tab.key ? 'text-fg-subtle/60' : 'text-fg-subtle/40'"
                >{{ tabCounts[tab.key] }}</span>
              </button>
            </template>
          </div>
          <button
            v-if="canWrite"
            @click="handleCreateClick"
            class="flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-medium text-[#1c1917]"
            style="background: linear-gradient(135deg, #c4683a, #d4785a)"
          >
            <Plus :size="15" />
            {{ activeTab === 'services' ? 'Создать сервис' : activeTab === 'processes' ? 'Создать политику' : 'Создать политику' }}
          </button>
        </div>
      </div>

      <!-- services tab -->
      <ServicesTab v-if="activeTab === 'services'" ref="servicesTabRef" />

      <!-- processes tab -->
      <ProcessesTab v-else-if="activeTab === 'processes'" ref="processesTabRef" />

      <!-- policies tab -->
      <template v-else>

      <!-- filters -->
      <div class="flex items-center gap-3 mb-6 flex-wrap">
        <div class="relative flex-1 min-w-[200px] max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/60 pointer-events-none" />
          <input
            v-model="searchQuery"
            placeholder="Поиск по названию..."
            class="h-9 w-full rounded-md border bg-bg-raised pl-9 pr-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none transition-colors duration-150"
            :class="searchQuery ? 'border-accent/40' : 'border-white/[0.08] focus:border-white/20'"
          />
        </div>

        <div class="flex gap-1.5">
          <button
            v-for="a in POLICY_ACTIONS" :key="a"
            @click="setAction(a)"
            class="h-8 px-3 rounded-md text-xs border transition-all duration-150"
            :class="activeAction === a
              ? a === 'block' ? 'border-red-700/50 bg-red-950/30 text-red-400' : 'border-emerald-700/50 bg-emerald-950/30 text-emerald-400'
              : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
          >
            <span class="flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full" :class="ACTION_STYLES[a].dot" />
              {{ ACTION_LABELS[a] }}
            </span>
          </button>
        </div>

        <div class="flex gap-1.5">
          <button
            v-for="s in POLICY_SOURCES" :key="s"
            @click="setSource(s)"
            class="h-8 px-3 rounded-md text-xs border transition-all duration-150"
            :class="activeSource === s ? SOURCE_STYLES[s] : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
          >
            {{ SOURCE_LABELS[s] }}
          </button>
        </div>

        <Transition
          enter-active-class="transition-all duration-150" enter-from-class="opacity-0 -translate-x-1"
          leave-active-class="transition-all duration-100" leave-to-class="opacity-0 -translate-x-1"
        >
          <button v-if="hasFilters" @click="resetFilters"
                  class="flex items-center gap-1 text-xs text-fg-subtle hover:text-fg transition-colors">
            <X :size="12" /> Сбросить
          </button>
        </Transition>

        <div class="ml-auto flex items-center gap-3">
          <span v-if="!store.isLoading && store.items.length" class="text-xs text-fg-subtle/60 tabular-nums flex items-center gap-1">
            {{ hasFilters ? `${filteredPolicies.length} из ${store.items.length}` : store.items.length }}
            <span class="opacity-40">·</span>
            <span class="text-emerald-400/50">{{ activeCount }} акт.</span>
          </span>
          <button
            @click="store.fetch()" :disabled="store.isLoading"
            class="h-8 w-8 flex items-center justify-center rounded-md border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
          >
            <RefreshCw :size="13" :class="store.isLoading ? 'animate-spin' : ''" />
          </button>
        </div>
      </div>

      <!-- sort + select-all bar -->
      <div v-if="filteredPolicies.length > 1" class="flex items-center gap-2 mb-3">
        <!-- select all (only when canWrite) -->
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

      <!-- content -->
      <UiLoadingOverlay :loading="store.isLoading && !!store.items.length" class="rounded-xl">

        <!-- skeleton -->
        <div v-if="store.isLoading && !store.items.length" class="flex flex-col gap-2">
          <div v-for="i in 5" :key="i"
               class="bg-bg-raised border border-white/[0.06] rounded-xl px-5 py-4 flex items-center gap-4">
            <Skeleton class="h-4 w-36 rounded bg-white/[0.05]" />
            <Skeleton class="h-5 w-16 rounded-md bg-white/[0.05]" />
            <Skeleton class="h-5 w-20 rounded-md bg-white/[0.05]" />
            <Skeleton class="h-3 w-24 rounded bg-white/[0.04] ml-auto" />
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
        <div v-else-if="!store.isLoading && !filteredPolicies.length"
             class="flex flex-col items-center justify-center py-20 gap-3">
          <ShieldCheck :size="26" :stroke-width="1.3" class="text-fg-subtle/40" />
          <p class="text-sm text-fg-subtle">
            {{ hasFilters ? 'Ничего не найдено — попробуйте изменить фильтры' : 'Политик пока нет' }}
          </p>
          <button v-if="hasFilters" @click="resetFilters" class="text-xs text-accent hover:text-accent-lit transition-colors">Сбросить фильтры</button>
          <button v-else-if="canWrite" @click="openCreate" class="text-xs text-accent hover:text-accent-lit transition-colors">Создать первую политику</button>
        </div>

        <!-- list -->
        <template v-else>
          <TransitionGroup tag="div" class="flex flex-col gap-2" @leave="onLeave">
            <div
              v-for="policy in pagedPolicies"
              :key="policy.id"
              class="group bg-bg-raised border rounded-xl overflow-hidden transition-colors duration-300"
              :class="[
                expandedId === policy.id ? 'border-white/[0.12]' : 'border-white/[0.06] hover:border-white/[0.10]',
                flashId === policy.id ? 'border-accent/40 bg-accent/[0.03]' : '',
              ]"
            >
              <!-- row header — clickable to expand -->
              <div
                class="flex items-center gap-4 px-5 py-3.5 cursor-pointer select-none"
                @click="toggleExpand(policy.id)"
              >
                <!-- checkbox — always rendered for column alignment -->
                <div class="shrink-0 w-4 h-4 flex items-center justify-center" @click.stop>
                  <button
                    v-if="canWrite && policy.source === 'local'"
                    type="button"
                    @click="toggleSelect(policy.id)"
                    class="w-4 h-4 rounded flex items-center justify-center border transition-all transition-opacity"
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
                  <Globe v-if="policy.source === 'global'" :size="15" class="text-blue-400/60" />
                  <Lock v-else :size="15" />
                </div>

                <!-- name + description -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium truncate transition-colors"
                          :class="policy.is_active ? 'text-fg' : 'text-fg-subtle/60'">
                      {{ policy.name }}
                    </span>
                  </div>
                  <p v-if="policy.description" class="text-xs text-fg-subtle/60 truncate mt-0.5">
                    {{ policy.description }}
                  </p>
                </div>

                <!-- badges -->
                <div class="flex items-center gap-2 shrink-0">
                  <span class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded border"
                        :class="ACTION_STYLES[policy.action].badge">
                    <ShieldOff v-if="policy.action === 'block'" :size="10" />
                    <ShieldCheck v-else :size="10" />
                    {{ ACTION_LABELS[policy.action] }}
                  </span>
                  <span class="text-xs px-2 py-0.5 rounded border" :class="SOURCE_STYLES[policy.source]">
                    {{ SOURCE_LABELS[policy.source] }}
                  </span>
                  <span v-if="policy.is_global"
                        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border
                               border-blue-800/40 bg-blue-950/30 text-blue-400">
                    <Globe :size="9" />
                    все агенты
                  </span>
                </div>

                <!-- rules count -->
                <span class="text-xs text-fg-subtle/50 shrink-0 tabular-nums w-20 text-right">
                  {{ policy.rules_count }} {{ rulesSuffix(policy.rules_count) }}
                </span>

                <!-- inline toggle (local only) -->
                <div v-if="canWrite && policy.source === 'local'"
                     class="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                     @click.stop>

                  <!-- active toggle switch -->
                  <button
                    @click="toggleActive(policy)"
                    :disabled="!!toggleLoading[policy.id]"
                    class="relative w-8 h-[18px] rounded-full border transition-all duration-200 disabled:opacity-50 shrink-0"
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

                  <!-- assign -->
                  <button
                    @click="openAssign(policy)"
                    class="p-1.5 rounded text-fg-subtle hover:text-accent hover:bg-accent/10 transition-colors"
                    title="Назначить"
                  >
                    <Target :size="13" />
                  </button>

                  <!-- duplicate -->
                  <button
                    @click="duplicatePolicy(policy)"
                    :disabled="!!duplicateLoading[policy.id]"
                    class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors disabled:opacity-40"
                    title="Дублировать"
                  >
                    <Loader2 v-if="duplicateLoading[policy.id]" :size="13" class="animate-spin" />
                    <Copy v-else :size="13" />
                  </button>

                  <!-- edit -->
                  <button
                    @click="openEdit(policy)"
                    class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors"
                    title="Редактировать"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>

                  <!-- delete -->
                  <button
                    @click="openDelete(policy)"
                    class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30 transition-colors"
                    title="Удалить"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14H6L5 6"/>
                      <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
                    </svg>
                  </button>
                </div>

                <!-- global read-only hint -->
                <span v-else-if="policy.source === 'global'"
                      class="text-xs text-fg-subtle/50 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  только чтение
                </span>

                <!-- chevron -->
                <ChevronDown
                  :size="14"
                  class="shrink-0 text-fg-subtle/40 transition-transform duration-200 ml-1"
                  :class="expandedId === policy.id ? 'rotate-180 text-fg-subtle/60' : ''"
                />
              </div>

              <!-- expanded rules -->
              <Transition
                enter-active-class="transition-all duration-200 ease-out"
                enter-from-class="opacity-0 -translate-y-1"
                leave-active-class="transition-all duration-150 ease-in"
                leave-to-class="opacity-0 -translate-y-1"
              >
                <div v-if="expandedId === policy.id"
                     class="border-t border-white/[0.06] px-5 py-3 bg-bg/40">

                  <div v-if="!policy.services?.length && !policy.custom_rules?.length"
                       class="text-xs text-fg-subtle/40 py-2 text-center">
                    Нет правил
                  </div>

                  <div v-else class="flex flex-col gap-4">

                    <!-- services chips -->
                    <div v-if="policy.services?.length">
                      <p class="text-xs uppercase tracking-wider text-fg-subtle/60 mb-1.5 select-none">
                        Сервисы
                      </p>
                      <div class="flex flex-wrap gap-1.5">
                        <span
                          v-for="svc in policy.services"
                          :key="svc.id"
                          class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border
                                 border-white/[0.08] bg-white/[0.03] text-fg-subtle select-none"
                        >
                          {{ svc.name }}
                          <span class="text-xs text-fg-subtle/60 tabular-nums">{{ svc.rules_count }}</span>
                        </span>
                      </div>
                    </div>

                    <!-- custom rules -->
                    <div v-if="policy.custom_rules?.length">
                      <p class="text-xs uppercase tracking-wider text-fg-subtle/60 mb-1.5 select-none">
                        Дополнительные правила
                      </p>

                      <!-- search -->
                      <div class="relative mb-2">
                        <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
                        <input
                          :value="rulesSearch[policy.id] ?? ''"
                          @input.stop="setRulesSearch(policy.id, $event.target.value)"
                          @click.stop
                          placeholder="Фильтр правил..."
                          class="h-7 w-full rounded-md border border-white/[0.06] bg-bg/60 pl-7 pr-7 text-xs text-fg
                                 placeholder:text-fg-subtle/30 focus:outline-none focus:border-white/15 transition-colors"
                        />
                        <button
                          v-if="rulesSearch[policy.id]"
                          @click.stop="setRulesSearch(policy.id, '')"
                          class="absolute right-2 top-1/2 -translate-y-1/2 text-fg-subtle/40 hover:text-fg-subtle transition-colors"
                        >
                          <X :size="11" />
                        </button>
                      </div>

                      <!-- groups -->
                      <template v-if="groupedCustomRules(policy).length">
                        <div v-for="group in groupedCustomRules(policy)" :key="group.type" class="mb-2">
                          <div class="flex items-center gap-1.5 mb-1.5">
                            <span class="text-xs uppercase tracking-wide text-fg-subtle/80 font-sans select-none">
                              {{ RULE_LABELS[group.type] }}
                            </span>
                            <span class="text-xs text-fg-subtle/60 tabular-nums select-none">
                              {{ group.searching ? group.matchedCount : group.total }}
                            </span>
                          </div>
                          <div class="flex flex-wrap gap-1">
                            <span
                              v-for="rule in group.shown"
                              :key="rule.value"
                              @click.stop="copyRule(rule.value)"
                              class="inline-flex items-center text-xs px-2 py-0.5 rounded border font-mono
                                     cursor-pointer select-none transition-all duration-150"
                              :class="[
                                RULE_TYPE_STYLES[group.type],
                                copiedRule === rule.value ? 'opacity-40 scale-95' : 'hover:brightness-125',
                              ]"
                              title="Копировать"
                            >
                              {{ rule.value }}
                            </span>
                          </div>
                          <button
                            v-if="!group.searching && group.total > GROUP_PREVIEW"
                            @click.stop="toggleGroup(policy.id, group.type)"
                            class="mt-1.5 text-xs text-fg-subtle/60 hover:text-fg-subtle transition-colors"
                          >
                            {{ expandedGroups[`${policy.id}:${group.type}`]
                                ? 'Свернуть'
                                : `+ ещё ${group.total - GROUP_PREVIEW}` }}
                          </button>
                        </div>
                      </template>

                      <div v-else class="py-3 text-center text-xs text-fg-subtle/40">
                        Ничего не найдено
                      </div>
                    </div>

                  </div>
                </div>
              </Transition>
            </div>
          </TransitionGroup>

          <UiPagination :page="page" :total-pages="totalPages" @go="goTo" />
        </template>

      </UiLoadingOverlay>

      </template><!-- end policies tab -->
    </div>

    <PolicyTestDialog v-model:open="testOpen" />

    <PolicyAssignDialog
      :open="!!assignTarget"
      :policy-id="assignTarget?.id"
      :policy-name="assignTarget?.name"
      @update:open="v => !v && (assignTarget = null)"
      @saved="store.fetch()"
    />

    <PolicyFormDialog
      v-model:open="formOpen"
      :form="formData"
      :target="formTarget"
      :loading="formLoading"
      :error="formError"
      @submit="submitForm"
    />

    <UiConfirmDialog
      :open="!!deleteTarget"
      variant="danger"
      title="Удаление политики"
      :description="`Удалить политику «${deleteTarget?.name}»? Это действие необратимо.`"
      confirm-text="Удалить"
      :loading="deleteLoading"
      @update:open="v => !v && closeDelete()"
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
        <button
          @click="bulkDuplicate"
          :disabled="bulkLoading"
          class="h-7 px-2.5 rounded-md text-xs border border-white/[0.08] text-fg-subtle
                 hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
        >
          Дублировать
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
