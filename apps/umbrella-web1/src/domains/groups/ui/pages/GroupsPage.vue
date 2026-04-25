<script setup>
import { Plus, Search, Layers, RefreshCw, X } from 'lucide-vue-next'
import { useGroupsPage }    from '@/domains/groups/useGroupsPage'
import { usePermissions }   from '@/shared/composables/usePermissions'
import GroupCard               from '@/domains/groups/ui/components/GroupCard.vue'
import GroupFormDialog         from '@/domains/groups/ui/components/GroupFormDialog.vue'
import GroupMembersDialog      from '@/domains/groups/ui/components/GroupMembersDialog.vue'

const {
  store,
  filteredGroups, pagedGroups, page, totalPages, goTo,
  searchQuery, hasFilters, resetFilters,
  formOpen, formTarget, formData, formLoading, formError,
  openCreate, openEdit, submitForm,
  deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
  membersOpen, membersTarget, membersList, membersLoading, membersError,
  addLoading, removeLoading, availableAgents,
  openMembers, addAgent, removeAgent,
} = useGroupsPage()

const { canWrite } = usePermissions()
</script>

<template>
  <div>
    <div class="px-8 py-8 max-w-6xl mx-auto w-full">

      <!-- header -->
      <div class="flex items-start justify-between mb-7">
        <div>
          <h1 class="text-4xl text-fg mb-1.5 leading-tight font-serif font-normal">Группы</h1>
          <p class="text-sm text-fg-subtle">Логическая группировка агентов.</p>
        </div>
        <button
          v-if="canWrite"
          @click="openCreate"
          class="flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-medium text-[#1c1917]"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          <Plus :size="15" />
          Создать группу
        </button>
      </div>

      <!-- filters -->
      <div class="flex items-center gap-3 mb-6">
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
              {{ filteredGroups.length }}<span v-if="hasFilters"> из {{ store.items.length }}</span>
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
               class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">
            <Skeleton class="h-1 w-full bg-white/[0.08]" />
            <div class="p-4 flex flex-col gap-3">
              <div class="flex items-center gap-2">
                <Skeleton class="w-2 h-2 rounded-full bg-white/[0.08]" />
                <Skeleton class="h-4 w-28 rounded bg-white/[0.05]" />
              </div>
              <Skeleton class="h-8 w-full rounded bg-white/[0.05]" />
              <Skeleton class="h-3 w-16 rounded bg-white/[0.05]" />
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
        <div v-else-if="!store.isLoading && !filteredGroups.length"
             class="flex flex-col items-center justify-center py-20 gap-3">
          <Layers :size="26" :stroke-width="1.3" class="text-fg-subtle/40" />
          <p class="text-sm text-fg-subtle">
            {{ hasFilters ? 'Ничего не найдено — попробуйте изменить фильтр' : 'Групп пока нет' }}
          </p>
          <button v-if="hasFilters" @click="resetFilters"
                  class="text-xs text-accent hover:text-accent-lit transition-colors">
            Сбросить фильтр
          </button>
          <button v-else @click="openCreate"
                  class="text-xs text-accent hover:text-accent-lit transition-colors">
            Создать первую группу
          </button>
        </div>

        <!-- grid -->
        <template v-else>
          <TransitionGroup
            tag="div"
            class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
            enter-active-class="transition-all duration-200"
            enter-from-class="opacity-0 scale-[0.98]"
            leave-active-class="transition-all duration-150"
            leave-to-class="opacity-0 scale-[0.97]"
          >
            <GroupCard
              v-for="group in pagedGroups"
              :key="group.id"
              :group="group"
              @edit="openEdit"
              @delete="openDelete"
              @members="openMembers"
            />
          </TransitionGroup>

          <UiPagination :page="page" :total-pages="totalPages" @go="goTo" />
        </template>

      </UiLoadingOverlay>
    </div>

  <!-- form dialog -->
  <GroupFormDialog
    v-model:open="formOpen"
    :form="formData"
    :target="formTarget"
    :loading="formLoading"
    :error="formError"
    @submit="submitForm"
  />

  <!-- members dialog -->
  <GroupMembersDialog
    v-model:open="membersOpen"
    :group="membersTarget"
    :members="membersList"
    :available="availableAgents"
    :loading="membersLoading"
    :error="membersError"
    :add-loading="addLoading"
    :remove-loading="removeLoading"
    @add="addAgent"
    @remove="removeAgent"
  />

  <!-- delete confirm -->
  <UiConfirmDialog
    :open="!!deleteTarget"
    variant="danger"
    title="Удаление группы"
    :description="`Удалить группу «${deleteTarget?.name}»? Это действие необратимо.`"
    confirm-text="Удалить"
    :loading="deleteLoading"
    @update:open="v => !v && closeDelete()"
    @confirm="confirmDelete"
  />
  </div>
</template>
