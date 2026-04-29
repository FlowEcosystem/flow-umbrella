<script setup>
import {
  ClipboardList, RefreshCw, User, Terminal, Trash2,
  LogIn, ChevronLeft, ChevronRight, Search, X, LogOut,
  Shield, Clock,
} from 'lucide-vue-next'
import { auditApi } from '@/domains/audit/api'

// ── Action metadata ───────────────────────────────────────────────────────────

const ACTIONS = {
  'command.issued': {
    label: 'Команда',
    icon:  Terminal,
    badge: 'bg-blue-950/50 text-blue-300 border-blue-800/30',
    dot:   'bg-blue-400',
    panel: 'border-blue-900/40',
  },
  'agent.deleted': {
    label: 'Агент удалён',
    icon:  Trash2,
    badge: 'bg-red-950/50 text-red-300 border-red-800/30',
    dot:   'bg-red-400',
    panel: 'border-red-900/40',
  },
  'agent.enrolled': {
    label: 'Регистрация',
    icon:  LogIn,
    badge: 'bg-emerald-950/50 text-emerald-300 border-emerald-800/30',
    dot:   'bg-emerald-400',
    panel: 'border-emerald-900/40',
  },
  'admin.login': {
    label: 'Вход',
    icon:  LogOut,
    badge: 'bg-white/[0.05] text-fg-subtle border-white/[0.10]',
    dot:   'bg-fg-subtle/40',
    panel: 'border-white/[0.10]',
  },
}

const FALLBACK_ACTION = {
  label: 'Событие',
  icon:  Shield,
  badge: 'bg-white/[0.04] text-fg-subtle/60 border-white/[0.08]',
  dot:   'bg-fg-subtle/30',
  panel: 'border-white/[0.08]',
}

const COMMAND_LABELS = {
  reboot:              'Перезагрузка',
  collect_diagnostics: 'Диагностика',
  update_self:         'Обновление агента',
  apply_config:        'Применить конфиг',
  sync_policies:       'Синхр. политик',
  decommission:        'Деинсталляция',
  kill_process:        'Завершить процесс',
}

// ── State ─────────────────────────────────────────────────────────────────────

const items   = ref([])
const total   = ref(0)
const loading = ref(false)
const page    = ref(1)
const LIMIT   = 50

const filterAction   = ref('')
const filterEmail    = ref('')
const filterDateFrom = ref('')
const filterDateTo   = ref('')

const expandedId  = ref(null)
const activePreset = ref(null) // 'today' | '7d' | '30d' | null

// ── Load ──────────────────────────────────────────────────────────────────────

async function load() {
  loading.value = true
  try {
    const params = { limit: LIMIT, offset: (page.value - 1) * LIMIT }
    if (filterAction.value)   params.action      = filterAction.value
    if (filterEmail.value)    params.admin_email  = filterEmail.value
    if (filterDateFrom.value) params.date_from    = filterDateFrom.value + 'T00:00:00'
    if (filterDateTo.value)   params.date_to      = filterDateTo.value   + 'T23:59:59'
    const data = await auditApi.list(params)
    items.value = data.items
    total.value = data.meta.total
  } catch { /* silent */ } finally {
    loading.value = false
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / LIMIT)))

const hasFilters = computed(() =>
  !!(filterAction.value || filterEmail.value || filterDateFrom.value || filterDateTo.value)
)

function toISO(d) { return d.toISOString().slice(0, 10) }

function setPreset(key) {
  const today = new Date()
  if (key === activePreset.value) {
    activePreset.value = null
    filterDateFrom.value = ''
    filterDateTo.value   = ''
    return
  }
  activePreset.value = key
  filterDateTo.value = toISO(today)
  if (key === 'today') {
    filterDateFrom.value = toISO(today)
  } else if (key === '7d') {
    const d = new Date(today); d.setDate(d.getDate() - 6)
    filterDateFrom.value = toISO(d)
  } else if (key === '30d') {
    const d = new Date(today); d.setDate(d.getDate() - 29)
    filterDateFrom.value = toISO(d)
  }
}

function clearAll() {
  filterAction.value   = ''
  filterEmail.value    = ''
  filterDateFrom.value = ''
  filterDateTo.value   = ''
  activePreset.value   = null
}

watch([filterAction, filterEmail, filterDateFrom, filterDateTo], () => { page.value = 1 })
watch([page, filterAction, filterEmail, filterDateFrom, filterDateTo], load)
onMounted(load)

// ── Format helpers ────────────────────────────────────────────────────────────

function fmtTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function fmtFull(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function timeAgo(iso) {
  if (!iso) return ''
  const sec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (sec <  60)  return `${sec} с назад`
  const min = Math.floor(sec / 60)
  if (min < 60)  return `${min} мин назад`
  const hr  = Math.floor(min / 60)
  if (hr  < 24)  return `${hr} ч назад`
  const day = Math.floor(hr / 24)
  if (day < 30)  return `${day} дн назад`
  return fmtDate(iso)
}

function shortId(id) { return id ? id.slice(0, 8) + '…' : null }

// One-line summary shown in the table row
function rowSummary(item) {
  const d = item.details ?? {}
  if (item.action === 'command.issued') {
    return COMMAND_LABELS[d.command_type] ?? d.command_type ?? '—'
  }
  if (item.action === 'agent.enrolled') return d.hostname ?? shortId(item.entity_id) ?? '—'
  if (item.action === 'agent.deleted')  return d.hostname ?? shortId(item.entity_id) ?? '—'
  if (item.action === 'admin.login')    return d.ip ?? '—'
  return shortId(item.entity_id) ?? '—'
}

// Secondary line shown in the table row
function rowSubtext(item) {
  const d = item.details ?? {}
  if (item.action === 'command.issued' && d.agent_id) return shortId(d.agent_id)
  if (item.action === 'agent.enrolled' && d.os)       return d.os
  if (item.action === 'agent.deleted'  && d.os)       return d.os
  if (item.action === 'admin.login'    && d.user_agent) {
    const m = d.user_agent.match(/^(\w+\/[\d.]+)/)
    return m ? m[1] : null
  }
  return null
}

// Structured detail rows for the expand panel
function detailRows(item) {
  const d = item.details ?? {}
  const rows = []

  if (item.action === 'command.issued') {
    rows.push({ label: 'Тип команды', value: COMMAND_LABELS[d.command_type] ?? d.command_type })
    if (d.agent_id) rows.push({ label: 'ID агента', value: d.agent_id, mono: true })
    if (d.payload && Object.keys(d.payload).length)
      rows.push({ label: 'Payload', value: JSON.stringify(d.payload, null, 2), mono: true, pre: true })
  } else if (item.action === 'agent.enrolled') {
    if (d.hostname) rows.push({ label: 'Hostname', value: d.hostname, mono: true })
    if (d.os)       rows.push({ label: 'Операционная система', value: d.os })
    if (d.ip)       rows.push({ label: 'IP-адрес', value: d.ip, mono: true })
  } else if (item.action === 'agent.deleted') {
    if (d.hostname) rows.push({ label: 'Hostname', value: d.hostname, mono: true })
    if (d.os)       rows.push({ label: 'Операционная система', value: d.os })
  } else if (item.action === 'admin.login') {
    if (d.ip)         rows.push({ label: 'IP-адрес', value: d.ip, mono: true })
    if (d.user_agent) rows.push({ label: 'User-Agent', value: d.user_agent, mono: true })
  } else {
    for (const [k, v] of Object.entries(d)) {
      const isObj = typeof v === 'object' && v !== null
      rows.push({ label: k, value: isObj ? JSON.stringify(v, null, 2) : String(v), mono: true, pre: isObj })
    }
  }

  return rows
}

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

// ── Filter options ────────────────────────────────────────────────────────────

const actionOptions = [
  { value: '',               label: 'Все действия' },
  { value: 'command.issued', label: 'Команды' },
  { value: 'agent.deleted',  label: 'Удаление агентов' },
  { value: 'agent.enrolled', label: 'Регистрации' },
  { value: 'admin.login',    label: 'Входы в систему' },
]
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto space-y-4">

    <!-- ── Header ── -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <ClipboardList :size="15" class="text-fg-subtle" />
        <span class="text-sm font-medium text-fg">Аудит-лог</span>
        <span v-if="total"
              class="text-[10px] font-medium text-fg-subtle/50 bg-white/[0.05]
                     border border-white/[0.07] rounded-full px-2 py-0.5 tabular-nums">
          {{ total.toLocaleString('ru-RU') }}
        </span>
      </div>
      <button @click="load" :disabled="loading"
              class="flex items-center gap-1.5 h-7 px-3 text-xs rounded-lg
                     bg-white/[0.04] hover:bg-white/[0.07] text-fg-subtle hover:text-fg
                     border border-white/[0.07] transition-colors disabled:opacity-40">
        <RefreshCw :size="11" :class="loading ? 'animate-spin' : ''" />
        Обновить
      </button>
    </div>

    <!-- ── Filters ── -->
    <div class="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 flex flex-wrap gap-2 items-center">

      <!-- action dropdown -->
      <UiSelect v-model="filterAction" :options="actionOptions"
                class="h-7 text-xs bg-transparent border border-white/[0.08] rounded-lg
                       px-2.5 text-fg-subtle hover:border-white/20" />

      <div class="w-px h-4 bg-white/[0.08]" />

      <!-- date presets -->
      <div class="flex items-center gap-1">
        <Clock :size="11" class="text-fg-subtle/40" />
        <button v-for="p in [['today','Сегодня'],['7d','7 дней'],['30d','30 дней']]" :key="p[0]"
                @click="setPreset(p[0])"
                class="h-7 px-2.5 text-xs rounded-lg border transition-colors"
                :class="activePreset === p[0]
                  ? 'bg-white/[0.08] text-fg border-white/20'
                  : 'bg-transparent text-fg-subtle/60 border-white/[0.07] hover:text-fg hover:border-white/20'">
          {{ p[1] }}
        </button>
      </div>

      <!-- custom date inputs -->
      <div class="flex items-center gap-1.5">
        <input v-model="filterDateFrom" type="date" @change="activePreset = null"
               class="h-7 rounded-lg border border-white/[0.08] bg-transparent px-2
                      text-xs text-fg-subtle/70 focus:outline-none focus:border-white/20
                      transition-colors [color-scheme:dark]" />
        <span class="text-xs text-fg-subtle/30">—</span>
        <input v-model="filterDateTo" type="date" @change="activePreset = null"
               class="h-7 rounded-lg border border-white/[0.08] bg-transparent px-2
                      text-xs text-fg-subtle/70 focus:outline-none focus:border-white/20
                      transition-colors [color-scheme:dark]" />
      </div>

      <div class="w-px h-4 bg-white/[0.08]" />

      <!-- email search -->
      <div class="relative">
        <Search :size="11" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/30 pointer-events-none" />
        <input v-model="filterEmail" placeholder="Поиск по email"
               class="h-7 w-44 rounded-lg border border-white/[0.08] bg-transparent pl-7 pr-6
                      text-xs text-fg placeholder:text-fg-subtle/30 focus:outline-none
                      focus:border-white/20 transition-colors" />
        <button v-if="filterEmail" @click="filterEmail = ''"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-fg-subtle/30 hover:text-fg-subtle">
          <X :size="10" />
        </button>
      </div>

      <!-- clear all -->
      <button v-if="hasFilters" @click="clearAll"
              class="ml-auto flex items-center gap-1.5 h-7 px-2.5 text-xs rounded-lg
                     border border-white/[0.07] text-fg-subtle/50 hover:text-red-400
                     hover:border-red-900/40 transition-colors">
        <X :size="10" />
        Сбросить
      </button>
    </div>

    <!-- ── Table ── -->
    <div class="rounded-xl border border-white/[0.07] overflow-hidden">

      <!-- column headers -->
      <div class="grid grid-cols-[180px_160px_1fr_200px] gap-4 px-5 py-2.5
                  border-b border-white/[0.06] bg-white/[0.02]">
        <span class="text-[11px] font-medium text-fg-subtle/40 uppercase tracking-wider">Время</span>
        <span class="text-[11px] font-medium text-fg-subtle/40 uppercase tracking-wider">Событие</span>
        <span class="text-[11px] font-medium text-fg-subtle/40 uppercase tracking-wider">Детали</span>
        <span class="text-[11px] font-medium text-fg-subtle/40 uppercase tracking-wider">Инициатор</span>
      </div>

      <!-- skeleton -->
      <div v-if="loading && !items.length" class="divide-y divide-white/[0.04]">
        <div v-for="i in 7" :key="i"
             class="grid grid-cols-[180px_160px_1fr_200px] gap-4 px-5 py-3.5 items-center">
          <div class="space-y-1.5">
            <div class="h-3 rounded bg-white/[0.06] w-16 animate-pulse" />
            <div class="h-2.5 rounded bg-white/[0.04] w-20 animate-pulse" />
          </div>
          <div class="h-5 rounded-full bg-white/[0.06] w-24 animate-pulse" />
          <div class="h-3 rounded bg-white/[0.05] w-36 animate-pulse" />
          <div class="h-3 rounded bg-white/[0.05] w-28 animate-pulse" />
        </div>
      </div>

      <!-- empty -->
      <div v-else-if="!items.length"
           class="py-16 flex flex-col items-center gap-2">
        <ClipboardList :size="24" class="text-fg-subtle/20" />
        <p class="text-xs text-fg-subtle/40">
          {{ hasFilters ? 'Ничего не найдено по заданным фильтрам' : 'Событий пока нет' }}
        </p>
        <button v-if="hasFilters" @click="clearAll"
                class="text-xs text-fg-subtle/50 hover:text-fg-subtle underline underline-offset-2 mt-1">
          Сбросить фильтры
        </button>
      </div>

      <!-- rows -->
      <div v-else class="divide-y divide-white/[0.04]">
        <div v-for="item in items" :key="item.id">

          <!-- ── Row ── -->
          <div
            class="grid grid-cols-[180px_160px_1fr_200px] gap-4 px-5 py-3.5 items-start
                   cursor-pointer transition-colors group"
            :class="expandedId === item.id
              ? 'bg-white/[0.03]'
              : 'hover:bg-white/[0.015]'"
            @click="toggleExpand(item.id)"
          >
            <!-- time -->
            <div class="flex flex-col gap-0.5" :title="fmtFull(item.created_at)">
              <span class="text-xs tabular-nums text-fg font-mono">
                {{ fmtTime(item.created_at) }}
              </span>
              <span class="text-[11px] tabular-nums text-fg-subtle/40">
                {{ fmtDate(item.created_at) }}
                <span class="text-fg-subtle/30">· {{ timeAgo(item.created_at) }}</span>
              </span>
            </div>

            <!-- action badge -->
            <div class="flex items-center pt-0.5">
              <span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px]
                           font-medium border whitespace-nowrap"
                    :class="(ACTIONS[item.action] ?? FALLBACK_ACTION).badge">
                <component :is="(ACTIONS[item.action] ?? FALLBACK_ACTION).icon"
                           :size="10" class="shrink-0 opacity-70" />
                {{ (ACTIONS[item.action] ?? FALLBACK_ACTION).label }}
              </span>
            </div>

            <!-- details -->
            <div class="flex flex-col gap-0.5 min-w-0 pt-0.5">
              <span class="text-xs text-fg truncate font-medium" :title="rowSummary(item)">
                {{ rowSummary(item) }}
              </span>
              <span v-if="rowSubtext(item)"
                    class="text-[11px] text-fg-subtle/50 font-mono truncate">
                {{ rowSubtext(item) }}
              </span>
            </div>

            <!-- initiator -->
            <div class="flex items-center gap-2 min-w-0 pt-0.5">
              <template v-if="item.admin_email">
                <div class="h-5 w-5 rounded-full bg-white/[0.08] flex items-center justify-center shrink-0">
                  <span class="text-[9px] font-semibold text-fg-subtle/70 uppercase">
                    {{ item.admin_email[0] }}
                  </span>
                </div>
                <span class="text-xs text-fg-subtle/70 truncate" :title="item.admin_email">
                  {{ item.admin_email }}
                </span>
              </template>
              <template v-else>
                <div class="h-5 w-5 rounded-full bg-white/[0.04] flex items-center justify-center shrink-0">
                  <Shield :size="9" class="text-fg-subtle/30" />
                </div>
                <span class="text-xs italic text-fg-subtle/35">система</span>
              </template>
            </div>
          </div>

          <!-- ── Expanded detail panel ── -->
          <div v-show="expandedId === item.id"
               class="border-l-2 mx-5 mb-4 rounded-r-lg overflow-hidden"
               :class="(ACTIONS[item.action] ?? FALLBACK_ACTION).panel">

            <!-- panel header -->
            <div class="flex items-center gap-2 px-5 py-3 bg-white/[0.02] border-b border-white/[0.05]">
              <component :is="(ACTIONS[item.action] ?? FALLBACK_ACTION).icon"
                         :size="12"
                         class="shrink-0 opacity-60"
                         :class="item.action === 'command.issued' ? 'text-blue-400'
                                 : item.action === 'agent.deleted' ? 'text-red-400'
                                 : item.action === 'agent.enrolled' ? 'text-emerald-400'
                                 : 'text-fg-subtle/50'" />
              <span class="text-xs font-medium text-fg">
                {{ (ACTIONS[item.action] ?? FALLBACK_ACTION).label }}
              </span>
              <span class="text-xs text-fg-subtle/40 ml-auto">{{ fmtFull(item.created_at) }}</span>
            </div>

            <!-- kv rows -->
            <div class="px-5 py-4 grid grid-cols-[160px_1fr] gap-x-4 gap-y-3">
              <template v-for="row in detailRows(item)" :key="row.label">
                <span class="text-[11px] text-fg-subtle/40 pt-0.5 self-start">{{ row.label }}</span>
                <div>
                  <pre v-if="row.pre"
                       class="text-[11px] font-mono text-fg-subtle/80 whitespace-pre-wrap break-all
                              bg-white/[0.03] border border-white/[0.05] rounded-md
                              px-2.5 py-2 leading-relaxed">{{ row.value }}</pre>
                  <span v-else class="text-xs text-fg-subtle/80 break-all"
                        :class="row.mono ? 'font-mono' : ''">{{ row.value }}</span>
                </div>
              </template>

              <!-- meta divider -->
              <div class="col-span-2 border-t border-white/[0.05] mt-1 pt-2.5 grid grid-cols-[160px_1fr] gap-x-4 gap-y-2">
                <span class="text-[11px] text-fg-subtle/25">ID записи</span>
                <span class="text-[11px] font-mono text-fg-subtle/35">{{ item.id }}</span>
                <template v-if="item.entity_id">
                  <span class="text-[11px] text-fg-subtle/25">Entity ID</span>
                  <span class="text-[11px] font-mono text-fg-subtle/35">{{ item.entity_id }}</span>
                </template>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="totalPages > 1"
         class="flex items-center justify-between text-xs text-fg-subtle/50">
      <span class="tabular-nums">
        {{ (page - 1) * LIMIT + 1 }}–{{ Math.min(page * LIMIT, total) }}
        из {{ total.toLocaleString('ru-RU') }}
      </span>
      <div class="flex items-center gap-1">
        <button @click="page--" :disabled="page === 1"
                class="h-7 px-3 rounded-lg bg-white/[0.04] hover:bg-white/[0.07]
                       text-fg-subtle hover:text-fg border border-white/[0.07]
                       transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
          <ChevronLeft :size="13" />
        </button>
        <span class="px-3 tabular-nums text-fg-subtle/60">{{ page }} / {{ totalPages }}</span>
        <button @click="page++" :disabled="page === totalPages"
                class="h-7 px-3 rounded-lg bg-white/[0.04] hover:bg-white/[0.07]
                       text-fg-subtle hover:text-fg border border-white/[0.07]
                       transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
          <ChevronRight :size="13" />
        </button>
      </div>
    </div>

  </div>
</template>
