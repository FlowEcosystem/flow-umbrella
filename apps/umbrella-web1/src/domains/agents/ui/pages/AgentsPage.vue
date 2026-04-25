<script setup>
import { Plus, Search, Monitor, RefreshCw, X } from 'lucide-vue-next'
import { useAgentsPage }    from '@/domains/agents/useAgentsPage'
import { useBulkAgents }    from '@/domains/agents/useBulkAgents'
import { usePermissions }   from '@/shared/composables/usePermissions'
import AgentCard            from '@/domains/agents/ui/components/AgentCard.vue'
import AgentBulkBar         from '@/domains/agents/ui/components/AgentBulkBar.vue'
import AgentCreateDialog    from '@/domains/agents/ui/components/AgentCreateDialog.vue'
import AgentEditDialog      from '@/domains/agents/ui/components/AgentEditDialog.vue'
import AgentTokenDialog     from '@/domains/agents/ui/components/AgentTokenDialog.vue'

const {
  store, filteredAgents, pagedAgents, page, totalPages, goTo,
  searchQuery, activeStatus, hasFilters,
  STATUS_LABELS, STATUS_DOT, AGENT_STATUSES,
  setStatus, resetFilters,
  createOpen, createForm, createLoading, createError, openCreate, submitCreate,
  editOpen, editForm, editLoading, editError, openEdit, submitEdit,
  tokenOpen, tokenData, tokenCopied, copyToken,
  regenTarget, regenLoading, openRegenConfirm, closeRegenConfirm, confirmRegen,
  deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
} = useAgentsPage()

const {
  selectedIds, selectedCount, hasSelection,
  bulkStatusLoading, bulkGroupLoading,
  toggle, isSelected, selectAll, clearSelection,
  bulkSetStatus, bulkAddToGroup,
} = useBulkAgents()

const { canWrite } = usePermissions()

const pagedIds = computed(() => pagedAgents.value.map(a => a.id))
const allPageSelected = computed(() =>
  pagedIds.value.length > 0 && pagedIds.value.every(id => isSelected(id))
)

function handleSelectAll() {
  if (allPageSelected.value) clearSelection()
  else selectAll(pagedIds.value)
}

watch(filteredAgents, () => clearSelection())
</script>

<template>
  <div>
    <div class="px-8 py-8 max-w-6xl mx-auto w-full">

      <!-- header -->
      <div class="flex items-start justify-between mb-7">
        <div>
          <h1 class="text-4xl text-fg mb-1.5 leading-tight font-serif font-normal">Агенты</h1>
          <p class="text-sm text-fg-subtle">Управление подключёнными устройствами.</p>
        </div>
        <button
          v-if="canWrite"
          @click="openCreate"
          class="flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-medium text-[#1c1917]"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          <Plus :size="15" />
          Добавить агента
        </button>
      </div>

      <!-- filters -->
      <div class="flex items-center gap-3 mb-6 flex-wrap">

        <div class="relative flex-1 min-w-[200px] max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/60 pointer-events-none" />
          <input
            v-model="searchQuery"
            placeholder="Поиск по hostname / IP..."
            class="h-9 w-full rounded-md border bg-bg-raised pl-9 pr-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none transition-colors duration-150"
            :class="searchQuery ? 'border-accent/40' : 'border-white/[0.08] focus:border-white/20'"
          />
        </div>

        <div class="flex gap-1.5">
          <button
            v-for="s in AGENT_STATUSES" :key="s"
            @click="setStatus(s)"
            class="h-8 px-3 rounded-md text-xs border transition-all duration-150"
            :class="activeStatus === s
              ? 'border-accent/50 bg-accent/10 text-accent'
              : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
          >
            <span class="inline-flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full" :class="STATUS_DOT[s]" />
              {{ STATUS_LABELS[s] }}
            </span>
          </button>
        </div>

        <Transition
          enter-active-class="transition-all duration-150"
          enter-from-class="opacity-0 -translate-x-1"
          leave-active-class="transition-all duration-100"
          leave-to-class="opacity-0 -translate-x-1"
        >
          <button v-if="hasFilters" @click="resetFilters"
                  class="flex items-center gap-1 text-xs text-fg-subtle hover:text-fg transition-colors">
            <X :size="12" /> Сбросить
          </button>
        </Transition>

        <div class="ml-auto flex items-center gap-3">
          <Transition
            enter-active-class="transition-opacity duration-200"
            enter-from-class="opacity-0"
            leave-active-class="transition-opacity duration-150"
            leave-to-class="opacity-0"
          >
            <span v-if="!store.isLoading && store.items.length" class="text-xs text-fg-subtle">
              {{ filteredAgents.length }}<span v-if="hasFilters"> из {{ store.items.length }}</span>
            </span>
          </Transition>

          <button
            @click="store.fetch()"
            :disabled="store.isLoading"
            class="h-8 w-8 flex items-center justify-center rounded-md border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
          >
            <RefreshCw :size="13" :class="store.isLoading ? 'animate-spin' : ''" />
          </button>
        </div>
      </div>

      <!-- content -->
      <UiLoadingOverlay :loading="store.isLoading && !!store.items.length" class="rounded-xl">

        <!-- skeleton -->
        <div v-if="store.isLoading && !store.items.length"
             class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="i in 6" :key="i"
               class="bg-bg-raised border border-white/[0.06] rounded-xl p-4 flex flex-col gap-3">
            <div class="flex items-center justify-between">
              <Skeleton class="h-5 w-20 rounded-md bg-white/[0.05]" />
              <Skeleton class="h-3 w-12 rounded bg-white/[0.05]" />
            </div>
            <Skeleton class="h-4 w-36 rounded bg-white/[0.05]" />
            <Skeleton class="h-3 w-24 rounded bg-white/[0.05]" />
            <div class="flex justify-between pt-1">
              <Skeleton class="h-3 w-20 rounded bg-white/[0.05]" />
              <Skeleton class="h-3 w-14 rounded bg-white/[0.05]" />
            </div>
          </div>
        </div>

        <!-- error -->
        <div v-else-if="store.error"
             class="flex flex-col items-center gap-3 py-16 text-center">
          <p class="text-sm text-red-400">{{ store.error }}</p>
          <button @click="store.fetch()"
                  class="text-xs text-fg-subtle hover:text-fg transition-colors underline">
            Попробовать снова
          </button>
        </div>

        <!-- empty -->
        <div v-else-if="!store.isLoading && !filteredAgents.length"
             class="flex flex-col items-center justify-center py-20 gap-3">
          <Monitor :size="26" :stroke-width="1.3" class="text-fg-subtle/40" />
          <p class="text-sm text-fg-subtle">
            {{ hasFilters ? 'Ничего не найдено — попробуйте изменить фильтры' : 'Агентов пока нет' }}
          </p>
          <button v-if="hasFilters" @click="resetFilters"
                  class="text-xs text-accent hover:text-accent-lit transition-colors">
            Сбросить фильтры
          </button>
          <button v-else @click="openCreate"
                  class="text-xs text-accent hover:text-accent-lit transition-colors">
            Добавить первого агента
          </button>
        </div>

        <!-- cards grid -->
        <template v-else>
          <TransitionGroup
            tag="div"
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
            enter-active-class="transition-all duration-200"
            enter-from-class="opacity-0 scale-[0.98]"
            leave-active-class="transition-all duration-150"
            leave-to-class="opacity-0 scale-[0.97]"
          >
            <AgentCard
              v-for="agent in pagedAgents"
              :key="agent.id"
              :agent="agent"
              :selected="isSelected(agent.id)"
              :any-selected="hasSelection"
              @select="toggle"
              @edit="openEdit"
              @regen="openRegenConfirm"
              @delete="openDelete"
            />
          </TransitionGroup>

          <UiPagination :page="page" :total-pages="totalPages" @go="goTo" />
        </template>

      </UiLoadingOverlay>

    </div>

  <AgentCreateDialog
    v-model:open="createOpen"
    :form="createForm"
    :loading="createLoading"
    :error="createError"
    @submit="submitCreate"
  />
  <AgentEditDialog
    v-model:open="editOpen"
    :form="editForm"
    :loading="editLoading"
    :error="editError"
    @submit="submitEdit"
  />
  <AgentTokenDialog
    v-model:open="tokenOpen"
    :data="tokenData"
    :copied="tokenCopied"
    @copy="copyToken"
  />

  <UiConfirmDialog
    :open="!!regenTarget"
    variant="warning"
    title="Перевыпуск enrollment token"
    :description="`Выпустить новый токен для ${regenTarget?.hostname}? Текущий токен станет недействительным.`"
    confirm-text="Выпустить токен"
    :loading="regenLoading"
    @update:open="v => !v && closeRegenConfirm()"
    @confirm="confirmRegen"
  />

  <UiConfirmDialog
    :open="!!deleteTarget"
    variant="danger"
    title="Удаление агента"
    :description="`Удалить агента ${deleteTarget?.hostname}? Это действие необратимо.`"
    confirm-text="Удалить"
    :loading="deleteLoading"
    @update:open="v => !v && closeDelete()"
    @confirm="confirmDelete"
  />

  <AgentBulkBar
    :selected-count="selectedCount"
    :total-count="pagedAgents.length"
    :all-selected="allPageSelected"
    :status-loading="bulkStatusLoading"
    :group-loading="bulkGroupLoading"
    @clear="clearSelection"
    @select-all="handleSelectAll"
    @set-status="bulkSetStatus"
    @add-to-group="bulkAddToGroup"
  />
  </div>
</template>
