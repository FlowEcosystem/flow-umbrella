<script setup>
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'
import { Search, Trash2 } from 'lucide-vue-next'

import { formatGroupUpdatedAt } from '@/domains/groups/groups.utils'

defineProps({
  activeGroup: {
    type: Object,
    default: null,
  },
  canWriteGroups: {
    type: Boolean,
    default: false,
  },
  membersLoading: {
    type: Boolean,
    default: false,
  },
  membersOffset: {
    type: Number,
    required: true,
  },
  membersLimit: {
    type: Number,
    required: true,
  },
  membersTotal: {
    type: Number,
    required: true,
  },
  groupAgents: {
    type: Array,
    required: true,
  },
  candidateAgents: {
    type: Array,
    required: true,
  },
  candidateSearch: {
    type: String,
    required: true,
  },
  candidateLoading: {
    type: Boolean,
    default: false,
  },
  selectedAgentIds: {
    type: Array,
    required: true,
  },
  addAgentsSubmitting: {
    type: Boolean,
    default: false,
  },
  removingAgentId: {
    type: String,
    default: null,
  },
  onSearchCandidateAgents: {
    type: Function,
    required: true,
  },
  onHandleMembersPageChange: {
    type: Function,
    required: true,
  },
  onAddAgentsToGroup: {
    type: Function,
    required: true,
  },
  onRemoveAgentFromGroup: {
    type: Function,
    required: true,
  },
})

const visible = defineModel('visible', { type: Boolean, default: false })
const candidateSearchModel = defineModel('candidateSearch', { type: String, default: '' })
const selectedAgentIdsModel = defineModel('selectedAgentIds', { type: Array, default: () => [] })
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="activeGroup ? `Состав группы: ${activeGroup.name}` : 'Состав группы'"
    :style="{ width: '960px', maxWidth: 'calc(100vw - 32px)' }"
  >
    <div v-if="activeGroup" class="members-dialog">
      <div class="members-summary">
        <div class="stacked-meta">
          <span class="field-label">Всего агентов</span>
          <strong>{{ activeGroup.agents_count }}</strong>
        </div>
        <div class="stacked-meta">
          <span class="field-label">Обновлена</span>
          <strong>{{ formatGroupUpdatedAt(activeGroup.updated_at) }}</strong>
        </div>
      </div>

      <div v-if="canWriteGroups" class="candidate-panel">
        <div class="candidate-panel__header">
          <div class="field field--search">
            <label class="field-label" for="candidate-search">Добавить агентов</label>
            <div class="search-field">
              <Search :size="16" class="search-field__icon" />
              <InputText
                id="candidate-search"
                v-model="candidateSearchModel"
                placeholder="Поиск по hostname"
                fluid
                @keyup.enter="onSearchCandidateAgents"
              />
            </div>
          </div>
          <Button label="Найти" severity="secondary" outlined :loading="candidateLoading" @click="onSearchCandidateAgents" />
        </div>

        <div class="candidate-list">
          <label v-for="agent in candidateAgents" :key="agent.id" class="candidate-item">
            <Checkbox v-model="selectedAgentIdsModel" :value="agent.id" />
            <div class="stacked-meta">
              <span>{{ agent.hostname }}</span>
              <span class="muted-text">{{ agent.notes || agent.os }}</span>
            </div>
          </label>
        </div>

        <div class="candidate-panel__actions">
          <Button
            label="Добавить выбранных"
            :disabled="!selectedAgentIdsModel.length"
            :loading="addAgentsSubmitting"
            @click="onAddAgentsToGroup"
          />
        </div>
      </div>

      <div class="members-table-wrap">
        <DataTable :value="groupAgents" data-key="id" class="domain-table" :loading="membersLoading">
          <Column header="Hostname">
            <template #body="{ data }">
              <div class="primary-cell">
                <span class="primary-cell__title">{{ data.hostname }}</span>
                <span class="primary-cell__hint">{{ data.notes || data.os }}</span>
              </div>
            </template>
          </Column>

          <Column header="Статус">
            <template #body="{ data }">
              <span class="muted-text">{{ data.status }}</span>
            </template>
          </Column>

          <Column header="Последний вход">
            <template #body="{ data }">
              <span class="muted-text">{{ data.last_seen_at ? formatGroupUpdatedAt(data.last_seen_at) : '—' }}</span>
            </template>
          </Column>

          <Column v-if="canWriteGroups" header="Действия" body-class="actions-col">
            <template #body="{ data }">
              <div class="row-actions">
                <Button
                  text
                  rounded
                  severity="danger"
                  aria-label="Убрать агента из группы"
                  :loading="removingAgentId === data.id"
                  @click="onRemoveAgentFromGroup(data)"
                >
                  <Trash2 :size="16" />
                </Button>
              </div>
            </template>
          </Column>
        </DataTable>

        <Paginator
          :rows="membersLimit"
          :total-records="membersTotal"
          :first="membersOffset"
          template="PrevPageLink CurrentPageReport NextPageLink"
          current-page-report-template="{first}-{last} из {totalRecords}"
          class="domain-paginator"
          @page="onHandleMembersPageChange"
        />
      </div>
    </div>

    <template #footer>
      <Button label="Закрыть" @click="visible = false" />
    </template>
  </Dialog>
</template>
