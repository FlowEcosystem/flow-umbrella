<script setup>
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Skeleton from 'primevue/skeleton'
import { Pencil, Plus, Trash2, Users, XCircle } from 'lucide-vue-next'

import { formatGroupUpdatedAt } from '@/domains/groups/groups.utils'

defineProps({
  groupsStore: {
    type: Object,
    required: true,
  },
  initialLoadFinished: {
    type: Boolean,
    default: false,
  },
  canWriteGroups: {
    type: Boolean,
    default: false,
  },
  onOpenCreate: {
    type: Function,
    required: true,
  },
  onOpenEdit: {
    type: Function,
    required: true,
  },
  onOpenMembers: {
    type: Function,
    required: true,
  },
  onConfirmDelete: {
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
  <section class="table-shell">
    <div v-if="!initialLoadFinished && groupsStore.isLoading" class="table-skeleton">
      <div v-for="row in 5" :key="row" class="table-skeleton__row">
        <Skeleton height="16px" width="180px" />
        <Skeleton height="16px" width="220px" />
        <Skeleton height="16px" width="64px" />
        <Skeleton height="16px" width="150px" />
        <div class="table-skeleton__actions">
          <Skeleton shape="circle" size="32px" />
          <Skeleton shape="circle" size="32px" />
          <Skeleton shape="circle" size="32px" />
        </div>
      </div>
    </div>

    <template v-else-if="groupsStore.items.length">
      <DataTable :value="groupsStore.items" data-key="id" class="domain-table">
        <Column header="Группа">
          <template #body="{ data }">
            <div class="primary-cell">
              <div class="group-name-row">
                <span class="color-dot" :style="{ backgroundColor: data.color || 'var(--color-surface-subtle)' }" />
                <span class="primary-cell__title">{{ data.name }}</span>
              </div>
              <span class="primary-cell__hint">{{ data.description || 'Без описания' }}</span>
            </div>
          </template>
        </Column>

        <Column header="Агенты">
          <template #body="{ data }">
            <span class="count-pill">{{ data.agents_count }}</span>
          </template>
        </Column>

        <Column header="Обновлена">
          <template #body="{ data }">
            <span class="muted-text">{{ formatGroupUpdatedAt(data.updated_at) }}</span>
          </template>
        </Column>

        <Column header="Состав">
          <template #body="{ data }">
            <Button text @click="onOpenMembers(data)">
              <Users :size="16" />
              <span>Открыть</span>
            </Button>
          </template>
        </Column>

        <Column v-if="canWriteGroups" header="Действия" body-class="actions-col">
          <template #body="{ data }">
            <div class="row-actions">
              <Button text rounded aria-label="Редактировать группу" @click="onOpenEdit(data)">
                <Pencil :size="16" />
              </Button>
              <Button text rounded severity="danger" aria-label="Удалить группу" @click="onConfirmDelete(data)">
                <Trash2 :size="16" />
              </Button>
            </div>
          </template>
        </Column>
      </DataTable>

      <Paginator
        :rows="groupsStore.limit"
        :total-records="groupsStore.total"
        :first="groupsStore.offset"
        template="PrevPageLink CurrentPageReport NextPageLink"
        current-page-report-template="{first}-{last} из {totalRecords}"
        class="domain-paginator"
        @page="onPageChange"
      />
    </template>

    <div v-else class="empty-state">
      <XCircle :size="44" class="empty-state__icon" />
      <h2 class="empty-state__title">Группы ещё не созданы</h2>
      <p class="empty-state__description">Создайте первую группу, чтобы собирать агентов по средам, ролям или командам.</p>
      <Button v-if="canWriteGroups" @click="onOpenCreate">
        <Plus :size="16" />
        <span>Создать группу</span>
      </Button>
    </div>

    <Message v-if="groupsStore.error && initialLoadFinished && !groupsStore.items.length" severity="error">
      Не удалось загрузить список групп.
    </Message>
  </section>
</template>
