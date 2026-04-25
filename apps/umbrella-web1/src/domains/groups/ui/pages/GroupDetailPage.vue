<script setup>
import {
  ArrowLeft, Pencil, Trash2,
  Users, Calendar,
  Plus, X, Search, Loader2,
  ShieldCheck, ShieldOff, Globe,
} from 'lucide-vue-next'
import { useGroupDetailPage } from '@/domains/groups/useGroupDetailPage'
import { usePermissions }     from '@/shared/composables/usePermissions'
import GroupFormDialog         from '@/domains/groups/ui/components/GroupFormDialog.vue'

const route = useRoute()
const id    = route.params.id

const {
  displayGroup, isLoading,
  members, membersLoading,
  policies, policiesLoading,
  agentsStore,
  addOpen, addSearch, addLoading, availableAgents, addMember,
  removeLoading, removeMember,
  assignOpen, assignSearch, assignLoading, availablePolicies, allPoliciesLoading,
  togglingPolicyId, openAssign, assignPolicy, unassignPolicy,
  editOpen, editForm, editLoading, editError, openEdit, submitEdit,
  deleteOpen, deleteLoading, confirmDelete,
  colorDotStyle, fallbackColor,
  STATUS_DOT, formatLastSeen,
} = useGroupDetailPage(id)

const { canWrite } = usePermissions()

const accentColor = computed(() =>
  displayGroup.value
    ? (displayGroup.value.color || fallbackColor(displayGroup.value.name))
    : '#6e6e6e'
)

function agentSuffix(n) {
  const mod10  = n % 10
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 19) return 'ов'
  if (mod10 === 1) return ''
  if (mod10 >= 2 && mod10 <= 4) return 'а'
  return 'ов'
}
</script>

<template>
  <div class="px-8 py-8 max-w-4xl mx-auto w-full">

    <!-- back -->
    <RouterLink to="/groups"
      class="inline-flex items-center gap-1.5 text-xs text-fg-subtle hover:text-fg transition-colors mb-7">
      <ArrowLeft :size="13" />
      Все группы
    </RouterLink>

    <!-- skeleton -->
    <div v-if="isLoading || !displayGroup" class="flex flex-col gap-4">
      <div class="flex items-center gap-3">
        <Skeleton class="w-3 h-3 rounded-full bg-white/[0.08]" />
        <Skeleton class="h-8 w-40 rounded-lg bg-white/[0.05]" />
      </div>
      <Skeleton class="h-4 w-64 rounded bg-white/[0.04]" />
      <Skeleton class="h-px w-full bg-white/[0.04] mt-2" />
      <div class="flex flex-col gap-2 mt-2">
        <Skeleton v-for="i in 4" :key="i" class="h-12 rounded-xl bg-white/[0.04]" />
      </div>
    </div>

    <template v-else>

      <!-- colored top bar (mirrors GroupCard) -->
      <div class="h-1 w-full rounded-full mb-6" :style="{ backgroundColor: accentColor }" />

      <!-- header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <div class="flex items-center gap-3 mb-1.5">
            <span class="w-3 h-3 rounded-full shrink-0"
                  :style="colorDotStyle(accentColor)" />
            <h1 class="text-4xl text-fg leading-tight font-serif font-normal">
              {{ displayGroup.name }}
            </h1>
          </div>
          <p class="text-sm text-fg-subtle pl-6">
            {{ displayGroup.description || 'Без описания' }}
          </p>
        </div>

        <div v-if="canWrite" class="flex items-center gap-2">
          <button @click="openEdit"
            class="flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors">
            <Pencil :size="13" />
            Редактировать
          </button>
          <button @click="deleteOpen = true"
            class="h-8 w-8 flex items-center justify-center rounded-lg border border-red-900/30
                   text-red-400/60 hover:text-red-400 hover:border-red-800/60 transition-colors"
            title="Удалить группу">
            <Trash2 :size="14" />
          </button>
        </div>
      </div>

      <!-- stats row -->
      <div class="grid grid-cols-2 gap-3 mb-5">

        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-4">
          <div class="flex items-center gap-2 mb-1.5">
            <Users :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Агентов</span>
          </div>
          <p class="text-2xl font-semibold text-fg">
            {{ displayGroup.agents_count ?? 0 }}
            <span class="text-sm font-normal text-fg-subtle ml-1">
              агент{{ agentSuffix(displayGroup.agents_count ?? 0) }}
            </span>
          </p>
        </div>

        <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-4">
          <div class="flex items-center gap-2 mb-1.5">
            <Calendar :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Создана</span>
          </div>
          <p class="text-sm text-fg">
            {{ new Date(displayGroup.created_at).toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' }) }}
          </p>
        </div>

      </div>

      <!-- members section -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">

        <!-- section header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
          <div class="flex items-center gap-2">
            <Users :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Участники</span>
          </div>
          <button
            v-if="canWrite"
            @click="addOpen = !addOpen"
            class="h-6 w-6 flex items-center justify-center rounded-md transition-colors"
            :class="addOpen
              ? 'bg-accent/20 text-accent border border-accent/30'
              : 'text-fg-subtle hover:text-fg hover:bg-white/[0.06] border border-transparent'"
            title="Добавить агента"
          >
            <component :is="addOpen ? X : Plus" :size="12" />
          </button>
        </div>

        <!-- add-agent panel -->
        <Transition
          enter-active-class="transition-all duration-150 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          leave-active-class="transition-all duration-100 ease-in"
          leave-to-class="opacity-0 -translate-y-1"
        >
          <div v-if="addOpen" class="border-b border-white/[0.05] bg-bg/40">
            <div class="px-4 pt-3 pb-2">
              <div class="relative">
                <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/50 pointer-events-none" />
                <input
                  v-model="addSearch"
                  placeholder="Поиск агента..."
                  autofocus
                  class="h-8 w-full rounded-md border border-white/[0.08] bg-bg pl-7 pr-3 text-xs text-fg
                         placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
                />
              </div>
            </div>

            <div v-if="agentsStore.isLoading" class="px-4 py-3 text-xs text-fg-subtle/50">
              Загрузка...
            </div>
            <div v-else-if="!availableAgents.length" class="px-4 py-3 text-xs text-fg-subtle/50">
              {{ addSearch ? 'Ничего не найдено' : 'Все агенты уже в группе' }}
            </div>
            <div v-else class="max-h-44 overflow-y-auto divide-y divide-white/[0.03]">
              <button
                v-for="agent in availableAgents"
                :key="agent.id"
                @click="addMember(agent.id)"
                :disabled="addLoading"
                class="w-full flex items-center gap-2.5 px-4 py-2.5 text-left
                       hover:bg-white/[0.03] transition-colors disabled:opacity-50"
              >
                <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="STATUS_DOT[agent.status]" />
                <span class="text-sm text-fg flex-1 font-mono truncate">{{ agent.hostname }}</span>
                <span class="text-xs text-fg-subtle/40 font-mono shrink-0">{{ agent.ip_address ?? '' }}</span>
                <Loader2 v-if="addLoading" :size="12" class="animate-spin text-fg-subtle shrink-0" />
                <Plus v-else :size="12" class="text-fg-subtle/40 shrink-0" />
              </button>
            </div>
          </div>
        </Transition>

        <!-- members list -->
        <div v-if="membersLoading" class="flex flex-col divide-y divide-white/[0.04]">
          <div v-for="i in 3" :key="i" class="flex items-center gap-3 px-4 py-3">
            <Skeleton class="w-1.5 h-1.5 rounded-full bg-white/[0.08]" />
            <Skeleton class="h-3.5 w-36 rounded bg-white/[0.05]" />
            <Skeleton class="h-3 w-20 rounded bg-white/[0.04] ml-auto" />
          </div>
        </div>

        <div v-else-if="!members.length"
             class="flex items-center justify-center py-10">
          <p class="text-xs text-fg-subtle/50">В группе нет агентов</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div
            v-for="agent in members"
            :key="agent.id"
            class="group/row flex items-center gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors"
          >
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="STATUS_DOT[agent.status]" />
            <RouterLink :to="`/agents/${agent.id}`"
              class="text-sm text-fg font-mono flex-1 truncate hover:text-accent transition-colors">
              {{ agent.hostname }}
            </RouterLink>
            <span class="text-xs text-fg-subtle/40 font-mono shrink-0">{{ agent.ip_address ?? '—' }}</span>
            <span class="text-xs text-fg-subtle/40 shrink-0 hidden group-hover/row:block">
              {{ formatLastSeen(agent.last_seen_at) }}
            </span>
            <button
              v-if="canWrite"
              @click="removeMember(agent.id)"
              :disabled="removeLoading[agent.id]"
              class="opacity-0 group-hover/row:opacity-100 p-1 rounded text-fg-subtle/40
                     hover:text-red-400 hover:bg-red-950/30 transition-all disabled:cursor-wait shrink-0"
              title="Убрать из группы"
            >
              <Loader2 v-if="removeLoading[agent.id]" :size="12" class="animate-spin" />
              <X v-else :size="12" />
            </button>
          </div>
        </div>

      </div>

      <!-- policies section -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden mt-3">

        <!-- header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
          <div class="flex items-center gap-2">
            <ShieldCheck :size="13" class="text-fg-subtle/60" />
            <span class="text-xs text-fg-subtle uppercase tracking-wider">Политики</span>
            <span v-if="policies.length" class="text-xs text-fg-subtle/50 tabular-nums">{{ policies.length }}</span>
          </div>
          <button
            v-if="canWrite"
            @click="openAssign"
            class="h-6 w-6 flex items-center justify-center rounded-md transition-colors"
            :class="assignOpen
              ? 'bg-accent/20 text-accent border border-accent/30'
              : 'text-fg-subtle hover:text-fg hover:bg-white/[0.06] border border-transparent'"
            title="Назначить политику"
          >
            <component :is="assignOpen ? X : Plus" :size="12" />
          </button>
        </div>

        <!-- assign-policy panel -->
        <Transition
          enter-active-class="transition-all duration-150 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          leave-active-class="transition-all duration-100 ease-in"
          leave-to-class="opacity-0 -translate-y-1"
        >
          <div v-if="assignOpen" class="border-b border-white/[0.05] bg-bg/40">
            <div class="px-4 pt-3 pb-2">
              <div class="relative">
                <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/50 pointer-events-none" />
                <input
                  v-model="assignSearch"
                  placeholder="Поиск политики..."
                  autofocus
                  class="h-8 w-full rounded-md border border-white/[0.08] bg-bg pl-7 pr-3 text-xs text-fg
                         placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
                />
              </div>
            </div>

            <div v-if="allPoliciesLoading" class="px-4 py-3 text-xs text-fg-subtle/50">
              Загрузка...
            </div>
            <div v-else-if="!availablePolicies.length" class="px-4 py-3 text-xs text-fg-subtle/50">
              {{ assignSearch ? 'Ничего не найдено' : 'Все политики уже назначены' }}
            </div>
            <div v-else class="max-h-44 overflow-y-auto divide-y divide-white/[0.03]">
              <button
                v-for="p in availablePolicies"
                :key="p.id"
                @click="assignPolicy(p.id)"
                :disabled="assignLoading"
                class="w-full flex items-center gap-2.5 px-4 py-2.5 text-left
                       hover:bg-white/[0.03] transition-colors disabled:opacity-50"
              >
                <span class="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded border shrink-0"
                      :class="p.action === 'block'
                        ? 'border-red-900/40 bg-red-950/50 text-red-400'
                        : 'border-emerald-900/40 bg-emerald-950/50 text-emerald-400'">
                  <ShieldOff v-if="p.action === 'block'" :size="8" />
                  <ShieldCheck v-else :size="8" />
                </span>
                <span class="text-sm text-fg flex-1 truncate">{{ p.name }}</span>
                <Loader2 v-if="assignLoading" :size="12" class="animate-spin text-fg-subtle shrink-0" />
                <Plus v-else :size="12" class="text-fg-subtle/40 shrink-0" />
              </button>
            </div>
          </div>
        </Transition>

        <!-- policies list -->
        <div v-if="policiesLoading" class="flex flex-col divide-y divide-white/[0.04]">
          <div v-for="i in 2" :key="i" class="flex items-center gap-3 px-4 py-3">
            <Skeleton class="h-5 w-16 rounded-md bg-white/[0.08]" />
            <Skeleton class="h-3.5 w-32 rounded bg-white/[0.05]" />
          </div>
        </div>

        <div v-else-if="!policies.length" class="flex items-center justify-center py-8">
          <p class="text-xs text-fg-subtle/50">Политик не назначено</p>
        </div>

        <div v-else class="divide-y divide-white/[0.04]">
          <div
            v-for="policy in policies"
            :key="policy.id"
            class="group/row flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors"
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

            <span class="text-xs text-fg-subtle/50 tabular-nums shrink-0">{{ policy.rules_count }} пр.</span>

            <button
              v-if="canWrite"
              @click="unassignPolicy(policy.id)"
              :disabled="togglingPolicyId === policy.id"
              class="opacity-0 group-hover/row:opacity-100 p-1 rounded text-fg-subtle/40
                     hover:text-red-400 hover:bg-red-950/30 transition-all disabled:cursor-wait shrink-0"
              title="Снять политику"
            >
              <Loader2 v-if="togglingPolicyId === policy.id" :size="12" class="animate-spin" />
              <X v-else :size="12" />
            </button>
          </div>
        </div>

      </div>

    </template>

    <!-- edit dialog -->
    <GroupFormDialog
      v-if="displayGroup"
      v-model:open="editOpen"
      :form="editForm"
      :target="displayGroup"
      :loading="editLoading"
      :error="editError"
      @submit="submitEdit"
    />

    <!-- delete confirm -->
    <UiConfirmDialog
      :open="deleteOpen"
      variant="danger"
      title="Удаление группы"
      :description="`Удалить группу «${displayGroup?.name}»? Это действие необратимо.`"
      confirm-text="Удалить"
      :loading="deleteLoading"
      @update:open="v => !v && (deleteOpen = false)"
      @confirm="confirmDelete"
    />
  </div>
</template>
