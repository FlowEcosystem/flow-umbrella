<script setup>
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Skeleton from 'primevue/skeleton'
import { CheckCircle2, Pencil, Plus, Trash2, UsersRound, XCircle } from 'lucide-vue-next'

import UiTooltip from '@/shared/ui/UiTooltip.vue'
import { getRoleLabel } from '@/app/access/rbac'

defineProps({
  adminsStore: {
    type: Object,
    required: true,
  },
  initialLoadFinished: {
    type: Boolean,
    default: false,
  },
  canManageAdmins: {
    type: Boolean,
    default: false,
  },
  isCurrentUser: {
    type: Function,
    required: true,
  },
  avatarLabel: {
    type: Function,
    required: true,
  },
  formatRelativeLastLogin: {
    type: Function,
    required: true,
  },
  onOpenEdit: {
    type: Function,
    required: true,
  },
  onConfirmDelete: {
    type: Function,
    required: true,
  },
  onOpenCreate: {
    type: Function,
    required: true,
  },
  onPageChange: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <div class="admins-page__content">
    <div v-if="!initialLoadFinished && adminsStore.isLoading" class="admins-table-skeleton">
      <div class="admins-table-skeleton__header">
        <Skeleton height="18px" width="30%" />
        <Skeleton height="18px" width="16%" />
        <Skeleton height="18px" width="12%" />
        <Skeleton height="18px" width="18%" />
        <Skeleton height="18px" width="14%" />
      </div>
      <div v-for="row in 5" :key="row" class="admins-table-skeleton__row">
        <div class="admins-table-skeleton__identity">
          <Skeleton shape="circle" size="40px" />
          <div class="admins-table-skeleton__identity-meta">
            <Skeleton height="14px" width="160px" />
            <Skeleton height="12px" width="220px" />
          </div>
        </div>
        <Skeleton height="28px" width="112px" />
        <Skeleton height="18px" width="96px" />
        <Skeleton height="16px" width="128px" />
        <div class="admins-table-skeleton__actions">
          <Skeleton shape="circle" size="32px" />
          <Skeleton shape="circle" size="32px" />
        </div>
      </div>
    </div>

    <template v-else-if="adminsStore.items.length">
      <DataTable
        :value="adminsStore.items"
        data-key="id"
        striped-rows
        class="admins-table"
        :loading="adminsStore.isLoading && !initialLoadFinished"
      >
        <Column header="Администратор">
          <template #body="{ data }">
            <div class="admin-identity">
              <div class="admin-avatar">
                <img v-if="data.avatar_url" :src="data.avatar_url" :alt="data.email" class="admin-avatar__image" />
                <span v-else class="admin-avatar__fallback">
                  {{ avatarLabel(data) }}
                </span>
              </div>

              <div class="admin-identity__meta">
                <div class="admin-identity__name-line">
                  <span class="admin-identity__name">{{ data.full_name || 'Без имени' }}</span>
                </div>
                <div class="admin-identity__email-line">
                  <span class="admin-identity__email">{{ data.email }}</span>
                  <span v-if="isCurrentUser(data)" class="self-badge">Это вы</span>
                </div>
              </div>
            </div>
          </template>
        </Column>

        <Column header="Роль">
          <template #body="{ data }">
            <span class="role-badge" :class="`role-badge--${data.role}`">
              {{ getRoleLabel(data.role) }}
            </span>
          </template>
        </Column>

        <Column header="Активен">
          <template #body="{ data }">
            <div v-if="data.is_active" class="status-indicator status-indicator--active">
              <CheckCircle2 :size="16" />
            </div>
            <div v-else class="status-indicator status-indicator--inactive">
              <XCircle :size="16" />
              <span>Деактивирован</span>
            </div>
          </template>
        </Column>

        <Column header="Последний вход">
          <template #body="{ data }">
            <span class="last-login" :class="{ 'is-muted': formatRelativeLastLogin(data.last_login_at).muted }">
              {{ formatRelativeLastLogin(data.last_login_at).text }}
            </span>
          </template>
        </Column>

        <Column header="Действия" body-class="admins-table__actions-col">
          <template #body="{ data }">
            <div class="row-actions">
              <Button text rounded aria-label="Редактировать администратора" @click="onOpenEdit(data)">
                <Pencil :size="16" />
              </Button>

              <UiTooltip v-if="isCurrentUser(data)" text="Нельзя удалить себя">
                <span class="row-actions__tooltip-wrap">
                  <Button text rounded severity="danger" disabled aria-label="Удалить администратора">
                    <Trash2 :size="16" />
                  </Button>
                </span>
              </UiTooltip>
              <Button
                v-else
                text
                rounded
                severity="danger"
                aria-label="Удалить администратора"
                @click="onConfirmDelete(data)"
              >
                <Trash2 :size="16" />
              </Button>
            </div>
          </template>
        </Column>
      </DataTable>

      <Paginator
        :rows="adminsStore.limit"
        :total-records="adminsStore.total"
        :first="adminsStore.offset"
        template="PrevPageLink CurrentPageReport NextPageLink"
        current-page-report-template="{first}-{last} из {totalRecords}"
        class="admins-paginator"
        @page="onPageChange"
      />
    </template>

    <div v-else class="admins-empty-state">
      <UsersRound :size="48" class="admins-empty-state__icon" />
      <h2 class="admins-empty-state__title">Пока нет администраторов</h2>
      <Button v-if="canManageAdmins" @click="onOpenCreate">
        <Plus :size="16" />
        <span>Добавить первого администратора</span>
      </Button>
    </div>

    <Message v-if="adminsStore.error && initialLoadFinished && !adminsStore.items.length" severity="error">
      Не удалось загрузить список администраторов.
    </Message>
  </div>
</template>
