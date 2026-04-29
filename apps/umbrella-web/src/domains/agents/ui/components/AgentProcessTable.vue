<script setup>
import {
  Search, Skull, ShieldBan, ChevronUp, ChevronDown, AlertTriangle, X,
  ShieldAlert, Gamepad2, Globe, MessageSquare, Code2, Cpu, Box,
} from 'lucide-vue-next'
import { classifyProcess, getDangerReason } from '@/shared/utils/processUtils'

const props = defineProps({
  processes:   { type: Array,  default: () => [] },
  killLoading: { type: Object, default: () => ({}) },
  canWrite:    { type: Boolean, default: false },
})

const emit = defineEmits(['kill', 'block'])

// ── Tabs ──────────────────────────────────────────────────────────────────────
const TABS = [
  { key: 'all',       label: 'Все',       icon: null,           activeText: 'text-fg',           activeBorder: 'border-white/40' },
  { key: 'dangerous', label: 'Угрозы',    icon: ShieldAlert,    activeText: 'text-red-400',      activeBorder: 'border-red-400'   },
  { key: 'games',     label: 'Игры',      icon: Gamepad2,       activeText: 'text-amber-400',    activeBorder: 'border-amber-400' },
  { key: 'browsers',  label: 'Браузеры',  icon: Globe,          activeText: 'text-blue-400',     activeBorder: 'border-blue-400'  },
  { key: 'comms',     label: 'Связь',     icon: MessageSquare,  activeText: 'text-sky-400',      activeBorder: 'border-sky-400'   },
  { key: 'dev',       label: 'Dev',       icon: Code2,          activeText: 'text-violet-400',   activeBorder: 'border-violet-400'},
  { key: 'other',     label: 'Прочее',    icon: Box,            activeText: 'text-fg-subtle',    activeBorder: 'border-white/30'  },
  { key: 'system',    label: 'Системные', icon: Cpu,            activeText: 'text-fg-subtle/70', activeBorder: 'border-white/20'  },
]

// Row styling per category (used in "Все" tab)
const CAT_STYLE = {
  dangerous: { rowBg: 'bg-red-950/10',          nameClass: 'text-red-300'       },
  games:     { rowBg: 'bg-amber-950/[0.06]',    nameClass: 'text-fg'            },
  browsers:  { rowBg: '',                        nameClass: 'text-fg'            },
  comms:     { rowBg: '',                        nameClass: 'text-fg'            },
  dev:       { rowBg: '',                        nameClass: 'text-fg'            },
  other:     { rowBg: '',                        nameClass: 'text-fg'            },
  system:    { rowBg: '',                        nameClass: 'text-fg-subtle/70'  },
}

// Counts per category (unfiltered, for tab badges)
const totalCounts = computed(() => {
  const r = { all: props.processes.length }
  for (const p of props.processes) {
    const cat = classifyProcess(p.name)
    r[cat] = (r[cat] ?? 0) + 1
  }
  return r
})

// Only show tabs that have processes
const visibleTabs = computed(() =>
  TABS.filter(t => t.key === 'all' || (totalCounts.value[t.key] ?? 0) > 0)
)

// Default tab: dangerous if it has items, else all
const activeTab = ref(null)
watch(() => props.processes, () => {
  if (activeTab.value !== null) return
  activeTab.value = (totalCounts.value.dangerous ?? 0) > 0 ? 'dangerous' : 'all'
}, { immediate: true })

// ── Sort ──────────────────────────────────────────────────────────────────────
const search  = ref('')
const sortKey = ref('mem_mb')
const sortDir = ref('desc')

function toggleSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'desc' }
}

// ── Displayed processes ───────────────────────────────────────────────────────
const displayedProcs = computed(() => {
  const q   = search.value.trim().toLowerCase()
  const tab = activeTab.value ?? 'all'
  let list  = props.processes

  if (tab !== 'all') list = list.filter(p => classifyProcess(p.name) === tab)
  if (q)             list = list.filter(p => p.name.toLowerCase().includes(q))

  return [...list].sort((a, b) => {
    const va = a[sortKey.value] ?? 0
    const vb = b[sortKey.value] ?? 0
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})

// Row helpers
function procCat(name)       { return classifyProcess(name) }
function procRowBg(name)     { return CAT_STYLE[procCat(name)]?.rowBg    ?? '' }
function procNameClass(name) { return CAT_STYLE[procCat(name)]?.nameClass ?? 'text-fg' }

// ── Kill confirmation ─────────────────────────────────────────────────────────
const confirmingKill  = ref(null)
const confirmingBlock = ref(null)
let _killTimer = null, _blockTimer = null

function requestKill(name) {
  if (confirmingKill.value === name) {
    clearTimeout(_killTimer); confirmingKill.value = null; emit('kill', name)
  } else {
    confirmingBlock.value = null; clearTimeout(_blockTimer)
    confirmingKill.value  = name
    clearTimeout(_killTimer)
    _killTimer = setTimeout(() => { confirmingKill.value = null }, 3000)
  }
}

function requestBlock(name) {
  if (confirmingBlock.value === name) {
    clearTimeout(_blockTimer); confirmingBlock.value = null; emit('block', name)
  } else {
    confirmingKill.value  = null; clearTimeout(_killTimer)
    confirmingBlock.value = name
    clearTimeout(_blockTimer)
    _blockTimer = setTimeout(() => { confirmingBlock.value = null }, 3000)
  }
}

onUnmounted(() => { clearTimeout(_killTimer); clearTimeout(_blockTimer) })

// ── Formatters ────────────────────────────────────────────────────────────────
function fmtMem(mb) {
  if (mb === 0)    return '< 1 МБ'
  if (mb >= 1024)  return (mb / 1024).toFixed(1) + ' ГБ'
  return mb + ' МБ'
}
function fmtCpu(pct) { return (pct ?? 0).toFixed(1) + '%' }

const gridCols = computed(() =>
  props.canWrite
    ? 'grid-cols-[1fr_60px_72px_80px_100px]'
    : 'grid-cols-[1fr_60px_72px_80px]'
)
</script>

<template>
  <div>

    <!-- tab bar -->
    <div class="flex items-end gap-0 border-b border-white/[0.06] mb-3 overflow-x-auto">
      <button
        v-for="tab in visibleTabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        class="flex items-center gap-1.5 px-3 py-2 text-xs border-b-2 whitespace-nowrap
               transition-colors shrink-0"
        :class="activeTab === tab.key
          ? [tab.activeText, tab.activeBorder]
          : 'text-fg-subtle/50 border-transparent hover:text-fg-subtle/80'"
      >
        <component v-if="tab.icon" :is="tab.icon" :size="11" />
        {{ tab.label }}
        <!-- count badge -->
        <span
          class="tabular-nums text-[10px] px-1 py-0.5 rounded transition-colors"
          :class="activeTab === tab.key
            ? (tab.key === 'dangerous' ? 'bg-red-500/20 text-red-300' : 'bg-white/[0.08] text-fg-subtle')
            : 'text-fg-subtle/30'"
        >
          {{ totalCounts[tab.key] ?? 0 }}
        </span>
        <!-- alert dot for dangerous tab when not active -->
        <span
          v-if="tab.key === 'dangerous' && activeTab !== 'dangerous' && (totalCounts.dangerous ?? 0) > 0"
          class="w-1.5 h-1.5 rounded-full bg-red-500 -ml-0.5"
        />
      </button>
    </div>

    <!-- search + count -->
    <div class="flex items-center gap-2 mb-2">
      <div class="relative flex-1">
        <Search :size="12" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
        <input
          v-model="search"
          placeholder="Поиск процесса..."
          class="w-full pl-8 pr-3 py-1.5 text-xs bg-white/[0.04] border border-white/[0.07]
                 rounded-lg text-fg placeholder:text-fg-subtle/30 focus:outline-none
                 focus:border-white/20 transition-colors"
        />
        <button v-if="search" @click="search = ''"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/40 hover:text-fg-subtle transition-colors">
          <X :size="11" />
        </button>
      </div>
      <span class="text-xs text-fg-subtle/40 shrink-0 tabular-nums">
        {{ displayedProcs.length }}<span v-if="search" class="opacity-60"> / {{ processes.length }}</span>
      </span>
    </div>

    <!-- column headers -->
    <div class="grid gap-2 px-3 py-1 mb-0.5" :class="gridCols">
      <button @click="toggleSort('name')"
              class="flex items-center gap-1 text-xs text-fg-subtle/40 hover:text-fg-subtle transition-colors text-left">
        Процесс
        <component :is="sortKey==='name' && sortDir==='asc' ? ChevronUp : ChevronDown"
                   :size="10" :class="sortKey==='name' ? 'text-fg-subtle' : 'opacity-0'" />
      </button>
      <span class="text-xs text-fg-subtle/40 text-right">PID</span>
      <button @click="toggleSort('cpu_percent')"
              class="flex items-center justify-end gap-1 text-xs text-fg-subtle/40 hover:text-fg-subtle transition-colors w-full">
        CPU
        <component :is="sortKey==='cpu_percent' && sortDir==='asc' ? ChevronUp : ChevronDown"
                   :size="10" :class="sortKey==='cpu_percent' ? 'text-fg-subtle' : 'opacity-0'" />
      </button>
      <button @click="toggleSort('mem_mb')"
              class="flex items-center justify-end gap-1 text-xs text-fg-subtle/40 hover:text-fg-subtle transition-colors w-full">
        Память
        <component :is="sortKey==='mem_mb' && sortDir==='asc' ? ChevronUp : ChevronDown"
                   :size="10" :class="sortKey==='mem_mb' ? 'text-fg-subtle' : 'opacity-0'" />
      </button>
      <span v-if="canWrite" class="text-xs text-fg-subtle/40 text-right">Действия</span>
    </div>

    <!-- rows -->
    <div class="divide-y divide-white/[0.04]">

      <div v-if="!displayedProcs.length" class="flex items-center justify-center py-8">
        <p class="text-xs text-fg-subtle/40">{{ search ? 'Ничего не найдено' : 'Данных нет' }}</p>
      </div>

      <div
        v-for="proc in displayedProcs"
        :key="proc.pid"
        class="grid gap-2 px-3 py-2 items-center hover:bg-white/[0.015] transition-colors"
        :class="[activeTab === 'all' ? procRowBg(proc.name) : '', gridCols]"
      >
        <!-- name -->
        <div class="flex items-center gap-1.5 min-w-0">
          <AlertTriangle
            v-if="procCat(proc.name) === 'dangerous'"
            :size="11" class="text-red-400 shrink-0"
            :title="getDangerReason(proc.name) ?? undefined"
          />
          <span
            class="text-xs font-mono truncate"
            :class="activeTab === 'all' ? procNameClass(proc.name) : (activeTab === 'dangerous' ? 'text-red-300' : activeTab === 'system' ? 'text-fg-subtle/70' : 'text-fg')"
            :title="proc.name"
          >{{ proc.name }}</span>
          <!-- danger reason (only on dangerous tab) -->
          <span v-if="activeTab === 'dangerous' && getDangerReason(proc.name)"
                class="text-[10px] text-red-400/40 truncate shrink min-w-0 hidden sm:block">
            {{ getDangerReason(proc.name) }}
          </span>
        </div>

        <!-- pid -->
        <span class="text-xs text-fg-subtle/50 tabular-nums text-right">{{ proc.pid }}</span>

        <!-- cpu -->
        <span class="text-xs tabular-nums text-right"
              :class="proc.cpu_percent > 50 ? 'text-yellow-400' : proc.cpu_percent > 10 ? 'text-fg-muted' : 'text-fg-subtle/50'">
          {{ fmtCpu(proc.cpu_percent) }}
        </span>

        <!-- mem -->
        <span class="text-xs tabular-nums text-right"
              :class="proc.mem_mb >= 1024 ? 'text-orange-400' : 'text-fg-subtle/70'">
          {{ fmtMem(proc.mem_mb) }}
        </span>

        <!-- actions -->
        <div v-if="canWrite" class="flex items-center justify-end gap-1">

          <Tooltip>
            <TooltipTrigger as-child>
              <button
                @click="requestKill(proc.name)"
                :disabled="!!killLoading[proc.name]"
                class="h-6 flex items-center gap-1 rounded px-2 text-[11px] font-medium
                       transition-all duration-150 disabled:opacity-30"
                :class="confirmingKill === proc.name
                  ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                  : 'text-fg-subtle/60 hover:text-red-400 hover:bg-red-950/30'"
              >
                <Skull :size="11" />
                <span v-if="confirmingKill === proc.name">Убить?</span>
              </button>
            </TooltipTrigger>
            <TooltipContent>
              {{ confirmingKill === proc.name ? 'Ещё раз — процесс будет завершён' : 'Завершить процесс' }}
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <button
                @click="requestBlock(proc.name)"
                class="h-6 flex items-center gap-1 rounded px-2 text-[11px] font-medium
                       transition-all duration-150"
                :class="confirmingBlock === proc.name
                  ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40'
                  : 'text-fg-subtle/60 hover:text-orange-400 hover:bg-orange-950/30'"
              >
                <ShieldBan :size="11" />
                <span v-if="confirmingBlock === proc.name">Блок?</span>
              </button>
            </TooltipTrigger>
            <TooltipContent>
              {{ confirmingBlock === proc.name ? 'Ещё раз — откроется форма политики' : 'Добавить в политику блокировки' }}
            </TooltipContent>
          </Tooltip>

        </div>
      </div>

    </div>

  </div>
</template>
