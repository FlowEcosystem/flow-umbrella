<script setup>
import { Plus, Search, UserCircle, RefreshCw, X, Pencil, Trash2, ShieldAlert } from 'lucide-vue-next'
import { ROLE_LABELS, ROLE_CLASSES, formatLastLogin } from '@/domains/admins/admins.utils'
import { useAdminsPage }   from '@/domains/admins/useAdminsPage'
import AdminFormDialog      from '@/domains/admins/ui/components/AdminFormDialog.vue'

const {
  store, auth,
  filteredAdmins, pagedAdmins, page, totalPages, goTo,
  searchQuery, hasFilters, resetFilters,
  formOpen, formTarget, formData, formLoading, formError,
  isEdit, openCreate, openEdit, submitForm,
  deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
  isSelf,
} = useAdminsPage()

function adminInitials(a) {
  const s = a.full_name ?? a.email ?? ''
  return s.split(/[\s@]/).map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'
}
</script>

<template>
  <div>
    <div class="px-8 py-8 max-w-5xl mx-auto w-full">

      <!-- header -->
      <div class="flex items-start justify-between mb-7">
        <div>
          <h1 class="text-4xl text-fg mb-1.5 leading-tight font-serif font-normal">Администраторы</h1>
          <p class="text-sm text-fg-subtle">Управление учётными записями и правами доступа.</p>
        </div>
        <button
          @click="openCreate"
          class="flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-medium text-[#1c1917]"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          <Plus :size="15" />
          Добавить
        </button>
      </div>

      <!-- filters -->
      <div class="flex items-center gap-3 mb-6">
        <div class="relative flex-1 min-w-[200px] max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/60 pointer-events-none" />
          <input
            v-model="searchQuery"
            placeholder="Поиск по email или имени..."
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
          <span v-if="!store.isLoading && store.items.length" class="text-xs text-fg-subtle">
            {{ filteredAdmins.length }}<span v-if="hasFilters"> из {{ store.items.length }}</span>
          </span>
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
             class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">
          <div v-for="i in 4" :key="i"
               class="flex items-center gap-4 px-5 py-3.5 border-b border-white/[0.04] last:border-0">
            <Skeleton class="w-8 h-8 rounded-full bg-white/[0.06]" />
            <div class="flex-1 flex flex-col gap-1.5">
              <Skeleton class="h-3.5 w-32 rounded bg-white/[0.05]" />
              <Skeleton class="h-3 w-48 rounded bg-white/[0.04]" />
            </div>
            <Skeleton class="h-5 w-20 rounded-full bg-white/[0.05]" />
            <Skeleton class="h-3 w-20 rounded bg-white/[0.04]" />
          </div>
        </div>

        <!-- error -->
        <div v-else-if="store.error"
             class="flex flex-col items-center gap-3 py-16 text-center">
          <ShieldAlert :size="24" :stroke-width="1.3" class="text-red-400/60" />
          <p class="text-sm text-red-400">{{ store.error }}</p>
          <button @click="store.fetch()"
                  class="text-xs text-fg-subtle hover:text-fg transition-colors underline">
            Попробовать снова
          </button>
        </div>

        <!-- empty -->
        <div v-else-if="!store.isLoading && !filteredAdmins.length"
             class="flex flex-col items-center justify-center py-20 gap-3">
          <UserCircle :size="26" :stroke-width="1.3" class="text-fg-subtle/40" />
          <p class="text-sm text-fg-subtle">
            {{ hasFilters ? 'Ничего не найдено' : 'Администраторов пока нет' }}
          </p>
          <button v-if="hasFilters" @click="resetFilters"
                  class="text-xs text-accent hover:text-accent-lit transition-colors">
            Сбросить фильтр
          </button>
        </div>

        <!-- table -->
        <template v-else>
        <div class="bg-bg-raised border border-white/[0.06] rounded-xl overflow-hidden">

          <!-- head -->
          <div class="grid grid-cols-[2fr_1fr_1fr_56px] gap-4 px-5 py-2.5
                      border-b border-white/[0.06] text-[11px] text-fg-subtle/50 uppercase tracking-wider">
            <span>Пользователь</span>
            <span>Роль</span>
            <span>Последний вход</span>
            <span />
          </div>

          <!-- rows -->
          <TransitionGroup
            tag="div"
            enter-active-class="transition-all duration-200"
            enter-from-class="opacity-0"
            leave-active-class="transition-all duration-150 absolute w-full"
            leave-to-class="opacity-0"
          >
            <div
              v-for="admin in pagedAdmins"
              :key="admin.id"
              class="grid grid-cols-[2fr_1fr_1fr_56px] gap-4 items-center px-5 py-3
                     border-b border-white/[0.04] last:border-0
                     hover:bg-white/[0.02] transition-colors"
            >
              <!-- user -->
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-8 h-8 rounded-full bg-accent-dim border border-accent/20
                            flex items-center justify-center shrink-0 text-xs text-accent font-medium">
                  {{ adminInitials(admin) }}
                </div>
                <div class="min-w-0">
                  <p class="text-sm text-fg truncate leading-tight">
                    {{ admin.full_name ?? admin.email }}
                    <span v-if="isSelf(admin)"
                          class="ml-1.5 text-[10px] text-fg-subtle/50 font-normal">(вы)</span>
                  </p>
                  <p v-if="admin.full_name" class="text-xs text-fg-subtle/60 truncate">{{ admin.email }}</p>
                </div>
              </div>

              <!-- role -->
              <div class="flex items-center gap-2">
                <span class="text-xs px-2 py-0.5 rounded border" :class="ROLE_CLASSES[admin.role]">
                  {{ ROLE_LABELS[admin.role] }}
                </span>
                <span v-if="!admin.is_active"
                      class="text-xs px-1.5 py-0.5 rounded border border-red-900/30 bg-red-950/30 text-red-400">
                  Неактивен
                </span>
              </div>

              <!-- last login -->
              <span class="text-xs text-fg-subtle/60">{{ formatLastLogin(admin.last_login_at) }}</span>

              <!-- actions -->
              <div class="flex items-center gap-0.5">
                <button
                  @click="openEdit(admin)"
                  title="Редактировать"
                  class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors"
                >
                  <Pencil :size="13" />
                </button>
                <button
                  v-if="!isSelf(admin)"
                  @click="openDelete(admin)"
                  title="Удалить"
                  class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30 transition-colors"
                >
                  <Trash2 :size="13" />
                </button>
              </div>
            </div>
          </TransitionGroup>
        </div>

        <UiPagination :page="page" :total-pages="totalPages" @go="goTo" />
        </template>

      </UiLoadingOverlay>
    </div>

    <!-- form dialog -->
    <AdminFormDialog
      v-model:open="formOpen"
      :form="formData"
      :is-edit="isEdit"
      :loading="formLoading"
      :error="formError"
      @submit="submitForm"
    />

    <!-- delete confirm -->
    <UiConfirmDialog
      :open="!!deleteTarget"
      variant="danger"
      title="Удаление администратора"
      :description="`Удалить аккаунт ${deleteTarget?.email}? Это действие необратимо.`"
      confirm-text="Удалить"
      :loading="deleteLoading"
      @update:open="v => !v && closeDelete()"
      @confirm="confirmDelete"
    />
  </div>
</template>
