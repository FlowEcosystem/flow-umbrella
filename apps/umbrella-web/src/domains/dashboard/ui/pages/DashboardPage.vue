<script setup>
import { Monitor, Users, ShieldCheck, Package, ArrowUpRight } from 'lucide-vue-next'
import { useDashboardPage } from '@/domains/dashboard/useDashboardPage'
import { STATUS_DOT, formatLastSeen } from '@/domains/agents/agents.utils'
import { fallbackColor, colorDotStyle } from '@/domains/groups/groups.utils'

const {
  agentsStore, groupsStore, policiesStore, servicesStore,
  totalAgents, activeAgents, statusBars, osBars,
  totalPolicies, activePolicies, inactivePolicies, blockPolicies, allowPolicies,
  totalServices,
  recentAgents, topGroups,
  greeting, todayDate,
} = useDashboardPage()
</script>

<template>
  <div class="px-8 py-8 max-w-5xl mx-auto w-full space-y-4">

    <!-- greeting -->
    <div class="flex items-end justify-between mb-2">
      <div>
        <h1 class="text-3xl text-fg leading-tight font-serif font-normal">{{ greeting }}</h1>
        <p class="text-sm text-fg-subtle mt-1 capitalize">{{ todayDate }}</p>
      </div>
    </div>

    <!-- 4 stat tiles -->
    <div class="grid grid-cols-4 gap-3">

      <RouterLink to="/agents"
        class="group bg-bg-raised border border-white/[0.06] rounded-xl p-4
               hover:border-white/[0.12] transition-colors">
        <div class="flex items-center justify-between mb-3">
          <div class="w-7 h-7 rounded-lg bg-emerald-950/60 border border-emerald-900/30
                      flex items-center justify-center">
            <Monitor :size="13" :stroke-width="1.5" class="text-emerald-400" />
          </div>
          <ArrowUpRight :size="12" class="text-fg-subtle/20 group-hover:text-fg-subtle/50 transition-colors" />
        </div>
        <div v-if="agentsStore.isLoading && !agentsStore.items.length">
          <div class="h-7 w-10 rounded bg-white/[0.05] mb-1.5" />
          <div class="h-3 w-16 rounded bg-white/[0.04]" />
        </div>
        <template v-else>
          <p class="text-2xl font-semibold text-fg tabular-nums">{{ totalAgents }}</p>
          <p class="text-xs text-fg-subtle/60 mt-0.5">{{ activeAgents }} активных</p>
        </template>
        <p class="text-[11px] uppercase tracking-wider text-fg-subtle/50 mt-3">Агенты</p>
      </RouterLink>

      <RouterLink to="/groups"
        class="group bg-bg-raised border border-white/[0.06] rounded-xl p-4
               hover:border-white/[0.12] transition-colors">
        <div class="flex items-center justify-between mb-3">
          <div class="w-7 h-7 rounded-lg bg-accent-dim border border-accent/20
                      flex items-center justify-center">
            <Users :size="13" :stroke-width="1.5" class="text-accent" />
          </div>
          <ArrowUpRight :size="12" class="text-fg-subtle/20 group-hover:text-fg-subtle/50 transition-colors" />
        </div>
        <div v-if="groupsStore.isLoading && !groupsStore.items.length">
          <div class="h-7 w-8 rounded bg-white/[0.05] mb-1.5" />
          <div class="h-3 w-20 rounded bg-white/[0.04]" />
        </div>
        <template v-else>
          <p class="text-2xl font-semibold text-fg tabular-nums">{{ groupsStore.items.length }}</p>
          <p class="text-xs text-fg-subtle/60 mt-0.5">групп создано</p>
        </template>
        <p class="text-[11px] uppercase tracking-wider text-fg-subtle/50 mt-3">Группы</p>
      </RouterLink>

      <RouterLink to="/policies"
        class="group bg-bg-raised border border-white/[0.06] rounded-xl p-4
               hover:border-white/[0.12] transition-colors">
        <div class="flex items-center justify-between mb-3">
          <div class="w-7 h-7 rounded-lg bg-violet-950/60 border border-violet-900/30
                      flex items-center justify-center">
            <ShieldCheck :size="13" :stroke-width="1.5" class="text-violet-400" />
          </div>
          <ArrowUpRight :size="12" class="text-fg-subtle/20 group-hover:text-fg-subtle/50 transition-colors" />
        </div>
        <div v-if="policiesStore.isLoading && !policiesStore.items.length">
          <div class="h-7 w-8 rounded bg-white/[0.05] mb-1.5" />
          <div class="h-3 w-16 rounded bg-white/[0.04]" />
        </div>
        <template v-else>
          <p class="text-2xl font-semibold text-fg tabular-nums">{{ totalPolicies }}</p>
          <p class="text-xs text-fg-subtle/60 mt-0.5">{{ activePolicies }} активных</p>
        </template>
        <p class="text-[11px] uppercase tracking-wider text-fg-subtle/50 mt-3">Политики</p>
      </RouterLink>

      <RouterLink :to="{ path: '/policies', query: { tab: 'services' } }"
        class="group bg-bg-raised border border-white/[0.06] rounded-xl p-4
               hover:border-white/[0.12] transition-colors">
        <div class="flex items-center justify-between mb-3">
          <div class="w-7 h-7 rounded-lg bg-cyan-950/60 border border-cyan-900/30
                      flex items-center justify-center">
            <Package :size="13" :stroke-width="1.5" class="text-cyan-400" />
          </div>
          <ArrowUpRight :size="12" class="text-fg-subtle/20 group-hover:text-fg-subtle/50 transition-colors" />
        </div>
        <div v-if="servicesStore.isLoading && !servicesStore.items.length">
          <div class="h-7 w-8 rounded bg-white/[0.05] mb-1.5" />
          <div class="h-3 w-16 rounded bg-white/[0.04]" />
        </div>
        <template v-else>
          <p class="text-2xl font-semibold text-fg tabular-nums">{{ totalServices }}</p>
          <p class="text-xs text-fg-subtle/60 mt-0.5">в каталоге</p>
        </template>
        <p class="text-[11px] uppercase tracking-wider text-fg-subtle/50 mt-3">Сервисы</p>
      </RouterLink>

    </div>

    <!-- middle row: agent status | OS + policy breakdown -->
    <div class="grid grid-cols-2 gap-3">

      <!-- agent status -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-5">
        <p class="text-xs uppercase tracking-widest text-fg-subtle/60 mb-4">Статус агентов</p>

        <div v-if="agentsStore.isLoading && !agentsStore.items.length" class="space-y-3">
          <div v-for="i in 4" :key="i" class="flex items-center gap-3">
            <div class="w-2 h-2 rounded-full bg-white/[0.06] shrink-0" />
            <div class="h-3 w-20 rounded bg-white/[0.05]" />
            <div class="h-1.5 flex-1 rounded-full bg-white/[0.04]" />
            <div class="h-3 w-5 rounded bg-white/[0.04]" />
          </div>
        </div>

        <template v-else>
          <!-- stacked bar -->
          <div class="flex h-1.5 rounded-full overflow-hidden gap-px mb-5">
            <template v-for="s in statusBars" :key="s.key">
              <div v-if="s.count > 0"
                   class="transition-all duration-700 first:rounded-l-full last:rounded-r-full"
                   :class="s.color"
                   :style="{ width: s.pct + '%' }" />
            </template>
          </div>

          <div class="space-y-3">
            <div v-for="s in statusBars" :key="s.key" class="flex items-center gap-2.5">
              <span class="w-2 h-2 rounded-full shrink-0" :class="s.dot" />
              <span class="text-xs text-fg-subtle flex-1">{{ s.label }}</span>
              <div class="w-24 bg-white/[0.04] rounded-full h-1">
                <div class="h-1 rounded-full transition-all duration-700"
                     :class="s.color"
                     :style="{ width: s.pct + '%' }" />
              </div>
              <span class="text-xs font-mono text-fg-subtle/50 w-6 text-right tabular-nums">{{ s.count }}</span>
            </div>
          </div>
        </template>
      </div>

      <!-- right: OS + policy actions -->
      <div class="flex flex-col gap-3">

        <!-- OS breakdown -->
        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-5 flex-1">
          <p class="text-xs uppercase tracking-widest text-fg-subtle/60 mb-4">ОС агентов</p>

          <div v-if="agentsStore.isLoading && !agentsStore.items.length" class="space-y-3">
            <div v-for="i in 3" :key="i" class="flex items-center gap-3">
              <div class="h-3 w-14 rounded bg-white/[0.05]" />
              <div class="h-1.5 flex-1 rounded-full bg-white/[0.04]" />
              <div class="h-3 w-4 rounded bg-white/[0.04]" />
            </div>
          </div>

          <div v-else class="space-y-3">
            <div v-for="o in osBars" :key="o.key" class="flex items-center gap-2.5">
              <span class="text-xs text-fg-subtle w-16 shrink-0">{{ o.label }}</span>
              <div class="flex-1 bg-white/[0.04] rounded-full h-1">
                <div class="h-1 rounded-full transition-all duration-700"
                     :class="o.color"
                     :style="{ width: o.pct + '%' }" />
              </div>
              <span class="text-xs font-mono text-fg-subtle/50 w-5 text-right tabular-nums">{{ o.count }}</span>
            </div>
          </div>
        </div>

        <!-- policy actions breakdown -->
        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-5">
          <p class="text-xs uppercase tracking-widest text-fg-subtle/60 mb-3">Политики</p>

          <div v-if="policiesStore.isLoading && !policiesStore.items.length"
               class="flex gap-5">
            <div v-for="i in 3" :key="i">
              <div class="h-6 w-8 rounded bg-white/[0.05] mb-1" />
              <div class="h-3 w-14 rounded bg-white/[0.04]" />
            </div>
          </div>

          <div v-else class="flex items-center gap-5">
            <div>
              <p class="text-xl font-semibold text-fg tabular-nums">{{ blockPolicies }}</p>
              <p class="text-xs text-fg-subtle/70 mt-0.5">блокировок</p>
            </div>
            <div class="w-px h-8 bg-white/[0.06]" />
            <div>
              <p class="text-xl font-semibold text-fg tabular-nums">{{ allowPolicies }}</p>
              <p class="text-xs text-fg-subtle/70 mt-0.5">разрешений</p>
            </div>
            <div class="w-px h-8 bg-white/[0.06]" />
            <div>
              <p class="text-xl font-semibold text-fg/40 tabular-nums">{{ inactivePolicies }}</p>
              <p class="text-xs text-fg-subtle/70 mt-0.5">неактивных</p>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- bottom row: recent agents | top groups -->
    <div class="grid grid-cols-[1fr_272px] gap-3">

      <!-- recent agents -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.05]">
          <span class="text-xs text-fg-subtle uppercase tracking-widest">Последняя активность</span>
          <RouterLink to="/agents"
            class="text-xs text-fg-subtle/50 hover:text-fg-subtle transition-colors">
            Все →
          </RouterLink>
        </div>

        <div v-if="agentsStore.isLoading && !agentsStore.items.length"
             class="divide-y divide-white/[0.04]">
          <div v-for="i in 6" :key="i" class="flex items-center gap-3 px-5 py-3">
            <div class="w-1.5 h-1.5 rounded-full bg-white/[0.08] shrink-0" />
            <div class="h-3.5 w-28 rounded bg-white/[0.05]" />
            <div class="h-3 w-20 rounded bg-white/[0.04] ml-auto" />
            <div class="h-3 w-16 rounded bg-white/[0.04]" />
          </div>
        </div>

        <div v-else-if="!recentAgents.length"
             class="flex items-center justify-center py-10">
          <p class="text-xs text-fg-subtle/50">Нет данных</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div v-for="agent in recentAgents" :key="agent.id"
               class="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02] transition-colors">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="STATUS_DOT[agent.status]" />
            <span class="text-sm text-fg font-mono truncate flex-1">{{ agent.hostname }}</span>
            <span class="text-xs text-fg-subtle/40 font-mono shrink-0">{{ agent.ip_address ?? '—' }}</span>
            <span class="text-xs text-fg-subtle/50 shrink-0 w-24 text-right">
              {{ formatLastSeen(agent.last_seen_at) }}
            </span>
          </div>
        </div>
      </div>

      <!-- top groups -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.05]">
          <span class="text-xs text-fg-subtle uppercase tracking-widest">Топ групп</span>
          <RouterLink to="/groups"
            class="text-xs text-fg-subtle/50 hover:text-fg-subtle transition-colors">
            Все →
          </RouterLink>
        </div>

        <div v-if="groupsStore.isLoading && !groupsStore.items.length"
             class="divide-y divide-white/[0.04]">
          <div v-for="i in 5" :key="i" class="flex items-center gap-3 px-5 py-3.5">
            <div class="w-2 h-2 rounded-full bg-white/[0.08]" />
            <div class="h-3.5 w-24 rounded bg-white/[0.05]" />
            <div class="h-3 w-6 rounded bg-white/[0.04] ml-auto" />
          </div>
        </div>

        <div v-else-if="!topGroups.length"
             class="flex items-center justify-center py-10">
          <p class="text-xs text-fg-subtle/50">Нет групп</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div v-for="group in topGroups" :key="group.id"
               class="flex items-center gap-3 px-5 py-3.5 hover:bg-white/[0.02] transition-colors">
            <span class="w-2 h-2 rounded-full shrink-0"
                  :style="colorDotStyle(group.color || fallbackColor(group.name))" />
            <span class="text-sm text-fg truncate flex-1">{{ group.name }}</span>
            <span class="text-xs text-fg-subtle/50 tabular-nums shrink-0">
              {{ group.agents_count ?? 0 }}
            </span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
