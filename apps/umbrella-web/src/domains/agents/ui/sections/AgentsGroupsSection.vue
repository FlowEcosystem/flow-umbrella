<script setup>
import Button from 'primevue/button'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Skeleton from 'primevue/skeleton'
import { Plus, XCircle } from 'lucide-vue-next'

import AgentGroupBlock from '@/domains/agents/ui/blocks/AgentGroupBlock.vue'

defineProps({
  initialLoadFinished: {
    type: Boolean,
    default: false,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  hasItems: {
    type: Boolean,
    default: false,
  },
  hasSourceItems: {
    type: Boolean,
    default: false,
  },
  groupedAgents: {
    type: Array,
    required: true,
  },
  canWriteAgents: {
    type: Boolean,
    default: false,
  },
  limit: {
    type: Number,
    required: true,
  },
  total: {
    type: Number,
    required: true,
  },
  offset: {
    type: Number,
    required: true,
  },
  error: {
    type: null,
    default: null,
  },
  isGroupCollapsed: {
    type: Function,
    required: true,
  },
  onToggleGroup: {
    type: Function,
    required: true,
  },
  setGroupRef: {
    type: Function,
    required: true,
  },
  isAgentBusy: {
    type: Function,
    required: true,
  },
  getPendingAgentActionLabel: {
    type: Function,
    required: true,
  },
  getPendingAgentAction: {
    type: Function,
    required: true,
  },
  onEdit: {
    type: Function,
    required: true,
  },
  onToken: {
    type: Function,
    required: true,
  },
  onMenu: {
    type: Function,
    required: true,
  },
  onPageChange: {
    type: Function,
    required: true,
  },
  onOpenCreate: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <div class="cards-shell">
    <div v-if="!initialLoadFinished && isLoading" class="cards-grid">
      <div v-for="row in 6" :key="row" class="agent-card agent-card--skeleton">
        <div class="agent-card__header">
          <div class="stacked-meta">
            <Skeleton height="18px" width="180px" />
            <Skeleton height="14px" width="120px" />
          </div>
          <Skeleton height="28px" width="112px" />
        </div>
        <div class="agent-card__meta-grid">
          <div class="stacked-meta">
            <Skeleton height="12px" width="64px" />
            <Skeleton height="16px" width="96px" />
          </div>
          <div class="stacked-meta">
            <Skeleton height="12px" width="72px" />
            <Skeleton height="16px" width="132px" />
          </div>
          <div class="stacked-meta">
            <Skeleton height="12px" width="92px" />
            <Skeleton height="16px" width="146px" />
          </div>
          <div class="stacked-meta">
            <Skeleton height="12px" width="84px" />
            <Skeleton height="16px" width="118px" />
          </div>
        </div>
        <div class="agent-card__actions">
          <Skeleton shape="circle" size="34px" />
          <Skeleton shape="circle" size="34px" />
          <Skeleton shape="circle" size="34px" />
        </div>
      </div>
    </div>

    <template v-else-if="hasItems">
      <AgentGroupBlock
        v-for="group in groupedAgents"
        :key="group.key"
        :group="group"
        :collapsed="isGroupCollapsed(group.key)"
        :can-write-agents="canWriteAgents"
        :set-group-ref="setGroupRef"
        :on-toggle="onToggleGroup"
        :is-agent-busy="isAgentBusy"
        :get-pending-agent-action-label="getPendingAgentActionLabel"
        :get-pending-agent-action="getPendingAgentAction"
        :on-edit="onEdit"
        :on-token="onToken"
        :on-menu="onMenu"
      />

      <Paginator
        :rows="limit"
        :total-records="total"
        :first="offset"
        template="PrevPageLink CurrentPageReport NextPageLink"
        current-page-report-template="{first}-{last} из {totalRecords}"
        class="domain-paginator"
        @page="onPageChange"
      />
    </template>

    <div v-else class="empty-state">
      <XCircle :size="44" class="empty-state__icon" />
      <template v-if="hasSourceItems">
        <h2 class="empty-state__title">Ничего не найдено</h2>
        <p class="empty-state__description">На текущей странице нет агентов, подходящих под выбранные фильтры.</p>
      </template>
      <template v-else>
        <h2 class="empty-state__title">Агенты ещё не добавлены</h2>
        <p class="empty-state__description">Создайте первый агент и выдайте enrollment token для установки.</p>
        <Button v-if="canWriteAgents" @click="onOpenCreate">
          <Plus :size="16" />
          <span>Добавить агента</span>
        </Button>
      </template>
    </div>

    <Message v-if="error && initialLoadFinished && !hasItems" severity="error">
      Не удалось загрузить список агентов.
    </Message>
  </div>
</template>
