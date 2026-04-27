<script setup>
import {
  ArrowLeft, Pencil, Trash2,
  Monitor, Clock, Calendar, Hash, FileText, Layers,
  Plus, X, Search, Loader2, ShieldCheck, ShieldOff, Globe,
  Terminal, RefreshCw, ShieldAlert, PowerOff, Cpu, MemoryStick, HardDrive,
} from 'lucide-vue-next'
import { useAgentDetailPage }      from '@/domains/agents/useAgentDetailPage'
import { usePermissions }          from '@/shared/composables/usePermissions'
import AgentEditDialog             from '@/domains/agents/ui/components/AgentEditDialog.vue'
import AgentCommandDialog          from '@/domains/agents/ui/components/AgentCommandDialog.vue'
import AgentOfflineTokenDialog     from '@/domains/agents/ui/components/AgentOfflineTokenDialog.vue'
import AgentMetricChart            from '@/domains/agents/ui/components/AgentMetricChart.vue'

const route = useRoute()
const id    = route.params.id

const {
  displayAgent, isLoading,
  groups, groupsLoading,
  policies, policiesLoading,
  commands, commandsLoading,
  groupsStore,
  addGroupOpen, addGroupSearch, addLoading, availableGroups, addToGroup,
  removeLoading, removeFromGroup,
  STATUS_LABELS, STATUS_CLASSES, STATUS_DOT, OS_LABELS,
  formatLastSeen, formatDate,
  colorDotStyle, fallbackColor,
  editOpen, editForm, editLoading, editError, openEdit, submitEdit,
  deleteOpen, deleteLoading, confirmDelete,
  COMMAND_TYPES, COMMAND_TYPE_LABELS, COMMAND_STATUS_LABELS,
  cmdOpen, cmdType, cmdPayload, cmdLoading, cmdError, openCmdDialog, submitCommand,
  offlineTokenOpen, offlineTokenData, offlineTokenLoading, offlineTokenCopied,
  generateOfflineToken, copyOfflineToken,
  decommissionOpen, decommissionLoading, confirmDecommission,
  metricsHistory, metricsLoading, latestMetric, metricPct,
} = useAgentDetailPage(id)

const { canWrite } = usePermissions()
</script>

<template>
  <div class="px-8 py-8 max-w-4xl mx-auto w-full">

    <!-- back -->
    <RouterLink to="/agents"
      class="inline-flex items-center gap-1.5 text-xs text-fg-subtle hover:text-fg transition-colors mb-7">
      <ArrowLeft :size="13" />
      Все агенты
    </RouterLink>

    <!-- skeleton -->
    <div v-if="isLoading || !displayAgent" class="flex flex-col gap-4">
      <Skeleton class="h-8 w-48 rounded-lg bg-white/[0.05]" />
      <Skeleton class="h-4 w-64 rounded bg-white/[0.04]" />
      <div class="grid grid-cols-2 gap-3 mt-4">
        <Skeleton v-for="i in 6" :key="i" class="h-20 rounded-xl bg-white/[0.04]" />
      </div>
    </div>

    <template v-else>

      <!-- header -->
      <div class="flex items-start justify-between mb-7">
        <div>
          <div class="flex items-center gap-3 mb-1.5">
            <h1 class="text-4xl text-fg leading-tight font-serif font-normal font-mono">
              {{ displayAgent.hostname ?? displayAgent.id.slice(0, 8) }}
            </h1>
            <span class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded border self-center"
                  :class="STATUS_CLASSES[displayAgent.status]">
              <span class="w-1.5 h-1.5 rounded-full" :class="STATUS_DOT[displayAgent.status]" />
              {{ STATUS_LABELS[displayAgent.status] }}
            </span>
          </div>
          <p class="text-sm text-fg-subtle">{{ OS_LABELS[displayAgent.os] ?? '—' }}</p>
        </div>

        <div v-if="canWrite" class="flex items-center gap-2">
          <button @click="openEdit"
            class="flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors">
            <Pencil :size="13" />
            Редактировать
          </button>

          <Tooltip v-if="displayAgent?.status === 'active'">
            <TooltipTrigger as-child>
              <button
                @click="generateOfflineToken"
                :disabled="offlineTokenLoading"
                class="h-8 w-8 flex items-center justify-center rounded-lg border border-white/[0.08]
                       text-fg-subtle hover:text-amber-400 hover:border-amber-800/40 transition-colors
                       disabled:opacity-40 disabled:cursor-wait">
                <ShieldAlert :size="14" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Offline-токен деинсталляции</TooltipContent>
          </Tooltip>

          <Tooltip v-if="displayAgent?.status === 'active'">
            <TooltipTrigger as-child>
              <button
                @click="decommissionOpen = true"
                class="h-8 w-8 flex items-center justify-center rounded-lg border border-red-900/30
                       text-red-400/60 hover:text-red-400 hover:border-red-800/60 transition-colors">
                <PowerOff :size="14" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Деинсталлировать агент</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <button @click="deleteOpen = true"
                :disabled="displayAgent?.status === 'active'"
                class="h-8 w-8 flex items-center justify-center rounded-lg border transition-colors
                       disabled:opacity-30 disabled:cursor-not-allowed"
                :class="displayAgent?.status === 'active'
                  ? 'border-white/[0.06] text-fg-subtle/40'
                  : 'border-white/[0.08] text-fg-subtle hover:text-red-400/60 hover:border-red-900/30'">
                <Trash2 :size="14" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              {{ displayAgent?.status === 'active'
                ? 'Нельзя удалить активного агента — сначала деинсталлируйте'
                : 'Удалить запись агента' }}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      <!-- info grid -->
      <div class="grid grid-cols-2 gap-3 mb-5">

        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-4">
          <div class="flex items-center gap-2 mb-1.5">
            <Monitor :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">IP-адрес</span>
          </div>
          <p class="text-sm text-fg font-mono">{{ displayAgent.ip_address ?? '—' }}</p>
        </div>

        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-4">
          <div class="flex items-center gap-2 mb-1.5">
            <Hash :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Версия агента</span>
          </div>
          <p class="text-sm text-fg font-mono">{{ displayAgent.agent_version ?? '—' }}</p>
        </div>

        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-4">
          <div class="flex items-center gap-2 mb-1.5">
            <Clock :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Последняя активность</span>
          </div>
          <p class="text-sm text-fg">{{ formatLastSeen(displayAgent.last_seen_at) }}</p>
          <p class="text-xs text-fg-subtle/50 mt-0.5">{{ formatDate(displayAgent.last_seen_at) }}</p>
        </div>

        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-4">
          <div class="flex items-center gap-2 mb-1.5">
            <Calendar :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Зарегистрирован</span>
          </div>
          <p class="text-sm text-fg">{{ formatDate(displayAgent.enrolled_at ?? displayAgent.created_at) }}</p>
        </div>

      </div>

      <!-- metrics -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden mb-5">
        <div class="flex items-center gap-2 px-4 py-3 border-b border-white/[0.05]">
          <Cpu :size="13" class="text-fg-subtle/60" />
          <span class="text-xs text-fg-subtle uppercase tracking-wider">Ресурсы</span>
          <span v-if="latestMetric" class="text-xs text-fg-subtle/40 ml-auto">
            {{ formatDate(latestMetric.collected_at) }}
          </span>
        </div>

        <div v-if="metricsLoading && !latestMetric" class="grid grid-cols-3 gap-px bg-white/[0.04]">
          <div v-for="i in 3" :key="i" class="bg-bg-raised px-4 py-4">
            <Skeleton class="h-3 w-16 rounded mb-3 bg-white/[0.06]" />
            <Skeleton class="h-1.5 w-full rounded-full bg-white/[0.05]" />
            <Skeleton class="h-16 w-full rounded mt-3 bg-white/[0.04]" />
          </div>
        </div>

        <div v-else-if="!latestMetric" class="flex items-center justify-center py-7">
          <p class="text-xs text-fg-subtle/60">Метрики ещё не получены</p>
        </div>

        <div v-else class="grid grid-cols-3 divide-x divide-white/[0.04]">

          <!-- CPU -->
          <div class="px-4 py-4">
            <div class="flex items-center gap-1.5 mb-2">
              <Cpu :size="11" class="text-fg-subtle/50" />
              <span class="text-xs text-fg-subtle/70 uppercase tracking-wider">CPU</span>
              <span class="text-sm text-fg font-mono ml-auto tabular-nums"
                    :class="latestMetric.cpu_percent > 80 ? 'text-red-400' : latestMetric.cpu_percent > 50 ? 'text-amber-400' : ''">
                {{ latestMetric.cpu_percent != null ? latestMetric.cpu_percent.toFixed(1) + '%' : '—' }}
              </span>
            </div>
            <div class="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden mb-3">
              <div class="h-full rounded-full transition-all duration-500"
                   :class="latestMetric.cpu_percent > 80 ? 'bg-red-400' : latestMetric.cpu_percent > 50 ? 'bg-amber-400' : 'bg-emerald-400'"
                   :style="{ width: (latestMetric.cpu_percent ?? 0) + '%' }" />
            </div>
            <div class="h-16">
              <AgentMetricChart :history="metricsHistory" field="cpu_percent"
                :color="latestMetric.cpu_percent > 80 ? '#f87171' : latestMetric.cpu_percent > 50 ? '#fbbf24' : '#34d399'" />
            </div>
          </div>

          <!-- RAM -->
          <div class="px-4 py-4">
            <div class="flex items-center gap-1.5 mb-2">
              <MemoryStick :size="11" class="text-fg-subtle/50" />
              <span class="text-xs text-fg-subtle/70 uppercase tracking-wider">RAM</span>
              <span class="text-sm text-fg font-mono ml-auto tabular-nums">
                {{ latestMetric.ram_total_mb ? metricPct(latestMetric.ram_used_mb, latestMetric.ram_total_mb) + '%' : '—' }}
              </span>
            </div>
            <div class="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden mb-1">
              <div class="h-full rounded-full transition-all duration-500 bg-sky-400"
                   :style="{ width: metricPct(latestMetric.ram_used_mb, latestMetric.ram_total_mb) + '%' }" />
            </div>
            <p v-if="latestMetric.ram_total_mb" class="text-xs text-fg-subtle/40 mb-2 tabular-nums">
              {{ Math.round(latestMetric.ram_used_mb / 1024) }} / {{ Math.round(latestMetric.ram_total_mb / 1024) }} ГБ
            </p>
            <div class="h-16">
              <AgentMetricChart :history="metricsHistory" field="ram_pct" color="#38bdf8" />
            </div>
          </div>

          <!-- Disk -->
          <div class="px-4 py-4">
            <div class="flex items-center gap-1.5 mb-2">
              <HardDrive :size="11" class="text-fg-subtle/50" />
              <span class="text-xs text-fg-subtle/70 uppercase tracking-wider">Диск</span>
              <span class="text-sm text-fg font-mono ml-auto tabular-nums"
                    :class="metricPct(latestMetric.disk_used_gb, latestMetric.disk_total_gb) > 90 ? 'text-red-400' : ''">
                {{ latestMetric.disk_total_gb ? metricPct(latestMetric.disk_used_gb, latestMetric.disk_total_gb) + '%' : '—' }}
              </span>
            </div>
            <div class="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden mb-1">
              <div class="h-full rounded-full transition-all duration-500"
                   :class="metricPct(latestMetric.disk_used_gb, latestMetric.disk_total_gb) > 90 ? 'bg-red-400' : 'bg-violet-400'"
                   :style="{ width: metricPct(latestMetric.disk_used_gb, latestMetric.disk_total_gb) + '%' }" />
            </div>
            <p v-if="latestMetric.disk_total_gb" class="text-xs text-fg-subtle/40 mb-2 tabular-nums">
              {{ latestMetric.disk_used_gb.toFixed(0) }} / {{ latestMetric.disk_total_gb.toFixed(0) }} ГБ
            </p>
            <div class="h-16">
              <AgentMetricChart :history="metricsHistory" field="disk_pct"
                :color="metricPct(latestMetric.disk_used_gb, latestMetric.disk_total_gb) > 90 ? '#f87171' : '#a78bfa'" />
            </div>
          </div>
        </div>
      </div>

      <!-- notes -->
      <div v-if="displayAgent.notes"
           class="bg-bg-raised border border-white/[0.06] rounded-xl p-4 mb-5">
        <div class="flex items-center gap-2 mb-2">
          <FileText :size="13" class="text-fg-subtle/60" />
          <span class="text-xs text-fg-subtle uppercase tracking-wider">Заметки</span>
        </div>
        <p class="text-sm text-fg-subtle whitespace-pre-wrap">{{ displayAgent.notes }}</p>
      </div>

      <!-- groups -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">

        <!-- section header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
          <div class="flex items-center gap-2">
            <Layers :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Группы</span>
          </div>
          <Tooltip v-if="canWrite">
            <TooltipTrigger as-child>
              <button
                @click="addGroupOpen = !addGroupOpen"
                class="h-6 w-6 flex items-center justify-center rounded-md transition-colors"
                :class="addGroupOpen
                  ? 'bg-accent/20 text-accent border border-accent/30'
                  : 'text-fg-subtle hover:text-fg hover:bg-white/[0.06] border border-transparent'"
              >
                <component :is="addGroupOpen ? X : Plus" :size="12" />
              </button>
            </TooltipTrigger>
            <TooltipContent>{{ addGroupOpen ? 'Закрыть' : 'Добавить в группу' }}</TooltipContent>
          </Tooltip>
        </div>

        <!-- add-to-group panel -->
        <Transition
          enter-active-class="transition-all duration-150 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          leave-active-class="transition-all duration-100 ease-in"
          leave-to-class="opacity-0 -translate-y-1"
        >
          <div v-if="addGroupOpen" class="border-b border-white/[0.05] bg-bg/40">
            <div class="px-4 pt-3 pb-2">
              <div class="relative">
                <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/50 pointer-events-none" />
                <input
                  v-model="addGroupSearch"
                  placeholder="Поиск группы..."
                  autofocus
                  class="h-8 w-full rounded-md border border-white/[0.08] bg-bg pl-7 pr-3 text-xs text-fg
                         placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
                />
              </div>
            </div>

            <div v-if="groupsStore.isLoading" class="px-4 py-3 text-xs text-fg-subtle/50">
              Загрузка...
            </div>
            <div v-else-if="!availableGroups.length" class="px-4 py-3 text-xs text-fg-subtle/50">
              {{ addGroupSearch ? 'Ничего не найдено' : 'Агент уже во всех группах' }}
            </div>
            <div v-else class="max-h-44 overflow-y-auto divide-y divide-white/[0.03]">
              <button
                v-for="g in availableGroups"
                :key="g.id"
                @click="addToGroup(g.id)"
                :disabled="addLoading"
                class="w-full flex items-center gap-2.5 px-4 py-2.5 text-left
                       hover:bg-white/[0.03] transition-colors disabled:opacity-50"
              >
                <span class="w-2 h-2 rounded-full shrink-0"
                      :style="colorDotStyle(g.color || fallbackColor(g.name))" />
                <span class="text-sm text-fg flex-1 truncate">{{ g.name }}</span>
                <Loader2 v-if="addLoading" :size="12" class="animate-spin text-fg-subtle shrink-0" />
                <Plus v-else :size="12" class="text-fg-subtle/40 shrink-0" />
              </button>
            </div>
          </div>
        </Transition>

        <!-- member groups list -->
        <div v-if="groupsLoading" class="flex flex-col divide-y divide-white/[0.04]">
          <div v-for="i in 2" :key="i" class="flex items-center gap-3 px-4 py-3">
            <Skeleton class="w-2.5 h-2.5 rounded-full bg-white/[0.08]" />
            <Skeleton class="h-3.5 w-28 rounded bg-white/[0.05]" />
          </div>
        </div>

        <div v-else-if="!groups.length"
             class="flex items-center justify-center py-8">
          <p class="text-xs text-fg-subtle/60">Агент не добавлен ни в одну группу</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div
            v-for="group in groups"
            :key="group.id"
            class="group/row flex items-center gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors"
          >
            <span class="w-2.5 h-2.5 rounded-full shrink-0"
                  :style="colorDotStyle(group.color || fallbackColor(group.name))" />
            <RouterLink :to="`/groups/${group.id}`"
              class="text-sm text-fg flex-1 truncate hover:text-accent transition-colors">
              {{ group.name }}
            </RouterLink>
            <span v-if="group.description" class="text-xs text-fg-subtle/60 truncate max-w-[180px] hidden group-hover/row:block">
              {{ group.description }}
            </span>
            <Tooltip v-if="canWrite">
              <TooltipTrigger as-child>
                <button
                  @click="removeFromGroup(group.id)"
                  :disabled="removeLoading[group.id]"
                  class="opacity-0 group-hover/row:opacity-100 p-1 rounded text-fg-subtle/40
                         hover:text-red-400 hover:bg-red-950/30 transition-all disabled:cursor-wait shrink-0"
                >
                  <Loader2 v-if="removeLoading[group.id]" :size="12" class="animate-spin" />
                  <X v-else :size="12" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Убрать из группы</TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>

      <!-- policies -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden mt-3">

        <div class="flex items-center gap-2 px-4 py-3 border-b border-white/[0.05]">
          <ShieldCheck :size="13" class="text-fg-subtle/60" />
          <span class="text-xs text-fg-subtle uppercase tracking-wider">Политики</span>
          <span v-if="policies.length"
                class="text-xs text-fg-subtle/50 tabular-nums">{{ policies.length }}</span>
        </div>

        <div v-if="policiesLoading" class="flex flex-col divide-y divide-white/[0.04]">
          <div v-for="i in 2" :key="i" class="flex items-center gap-3 px-4 py-3">
            <Skeleton class="h-5 w-16 rounded-md bg-white/[0.08]" />
            <Skeleton class="h-3.5 w-32 rounded bg-white/[0.05]" />
          </div>
        </div>

        <div v-else-if="!policies.length"
             class="flex items-center justify-center py-7">
          <p class="text-xs text-fg-subtle/60">Нет применимых политик</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div
            v-for="policy in policies"
            :key="policy.id"
            class="flex items-center gap-3 px-4 py-2.5"
          >
            <!-- action badge -->
            <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border shrink-0"
                  :class="policy.action === 'block'
                    ? 'border-red-900/40 bg-red-950/50 text-red-400'
                    : 'border-emerald-900/40 bg-emerald-950/50 text-emerald-400'">
              <ShieldOff v-if="policy.action === 'block'" :size="9" />
              <ShieldCheck v-else :size="9" />
              {{ policy.action === 'block' ? 'Блок' : 'Разр.' }}
            </span>

            <!-- name -->
            <span class="text-sm text-fg flex-1 truncate"
                  :class="policy.is_active ? '' : 'opacity-40'">
              {{ policy.name }}
            </span>

            <!-- global badge -->
            <span v-if="policy.is_global"
                  class="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded border
                         border-blue-800/40 bg-blue-950/30 text-blue-400 shrink-0">
              <Globe :size="9" />
              глоб.
            </span>

            <!-- rules count -->
            <span class="text-xs text-fg-subtle/50 tabular-nums shrink-0">
              {{ policy.rules_count }} пр.
            </span>
          </div>
        </div>
      </div>

      <!-- commands -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden mt-3">

        <div class="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
          <div class="flex items-center gap-2">
            <Terminal :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Команды</span>
            <span v-if="commands.length" class="text-xs text-fg-subtle/50 tabular-nums">{{ commands.length }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <Tooltip>
              <TooltipTrigger as-child>
                <button
                  @click="fetchCommands"
                  :disabled="commandsLoading"
                  class="h-6 w-6 flex items-center justify-center rounded-md text-fg-subtle/50
                         hover:text-fg hover:bg-white/[0.06] transition-colors disabled:opacity-40"
                >
                  <RefreshCw :size="11" :class="commandsLoading ? 'animate-spin' : ''" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Обновить список команд</TooltipContent>
            </Tooltip>
            <Tooltip v-if="canWrite">
              <TooltipTrigger as-child>
                <button
                  @click="openCmdDialog"
                  class="h-6 w-6 flex items-center justify-center rounded-md transition-colors
                         text-fg-subtle hover:text-fg hover:bg-white/[0.06] border border-transparent"
                >
                  <Plus :size="12" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Отправить команду</TooltipContent>
            </Tooltip>
          </div>
        </div>

        <div v-if="commandsLoading" class="flex flex-col divide-y divide-white/[0.04]">
          <div v-for="i in 2" :key="i" class="flex items-center gap-3 px-4 py-3">
            <Skeleton class="h-5 w-20 rounded-md bg-white/[0.08]" />
            <Skeleton class="h-3.5 w-28 rounded bg-white/[0.05]" />
            <Skeleton class="h-3.5 w-16 rounded bg-white/[0.04] ml-auto" />
          </div>
        </div>

        <div v-else-if="!commands.length" class="flex items-center justify-center py-7">
          <p class="text-xs text-fg-subtle/60">Команд ещё не отправлялось</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div
            v-for="cmd in commands"
            :key="cmd.id"
            class="flex items-center gap-3 px-4 py-2.5"
          >
            <!-- type -->
            <span class="text-sm text-fg font-mono flex-1 truncate">
              {{ COMMAND_TYPE_LABELS[cmd.type] ?? cmd.type }}
            </span>

            <!-- status -->
            <span class="text-xs px-2 py-0.5 rounded border shrink-0"
                  :class="{
                    'border-yellow-900/40 bg-yellow-950/40 text-yellow-400': cmd.status === 'pending' || cmd.status === 'sent' || cmd.status === 'acknowledged',
                    'border-emerald-900/40 bg-emerald-950/50 text-emerald-400': cmd.status === 'success',
                    'border-red-900/40 bg-red-950/50 text-red-400': cmd.status === 'failure' || cmd.status === 'timeout',
                  }">
              {{ COMMAND_STATUS_LABELS[cmd.status] ?? cmd.status }}
            </span>

            <!-- error -->
            <span v-if="cmd.error_message"
                  class="text-xs text-red-400/70 truncate max-w-[140px] shrink-0"
                  :title="cmd.error_message">
              {{ cmd.error_message }}
            </span>

            <!-- created at -->
            <span class="text-xs text-fg-subtle/40 tabular-nums shrink-0">
              {{ formatDate(cmd.created_at) }}
            </span>
          </div>
        </div>

      </div>

    </template>

    <!-- dialogs -->
    <AgentEditDialog
      v-if="displayAgent"
      v-model:open="editOpen"
      :form="editForm"
      :loading="editLoading"
      :error="editError"
      @submit="submitEdit"
    />

    <UiConfirmDialog
      :open="deleteOpen"
      variant="danger"
      title="Удаление агента"
      :description="`Удалить агента ${displayAgent?.hostname ?? displayAgent?.id?.slice(0,8)}? Это действие необратимо.`"
      confirm-text="Удалить"
      :loading="deleteLoading"
      @update:open="v => !v && (deleteOpen = false)"
      @confirm="confirmDelete"
    />

    <AgentCommandDialog
      :open="cmdOpen"
      :command-types="COMMAND_TYPES"
      :type-labels="COMMAND_TYPE_LABELS"
      :type="cmdType"
      :payload="cmdPayload"
      :loading="cmdLoading"
      :error="cmdError"
      @update:open="v => !v && (cmdOpen = false)"
      @update:type="cmdType = $event"
      @update:payload="cmdPayload = $event"
      @submit="submitCommand"
    />

    <AgentOfflineTokenDialog
      v-model:open="offlineTokenOpen"
      :data="offlineTokenData"
      :copied="offlineTokenCopied"
      @copy="copyOfflineToken"
    />

    <UiConfirmDialog
      :open="decommissionOpen"
      variant="danger"
      title="Деинсталляция агента"
      :description="`Отправить команду деинсталляции агенту ${displayAgent?.hostname ?? displayAgent?.id?.slice(0,8)}? Агент удалит себя с хоста. Это действие необратимо.`"
      confirm-text="Деинсталлировать"
      :loading="decommissionLoading"
      @update:open="v => !v && (decommissionOpen = false)"
      @confirm="confirmDecommission"
    />
  </div>
</template>
