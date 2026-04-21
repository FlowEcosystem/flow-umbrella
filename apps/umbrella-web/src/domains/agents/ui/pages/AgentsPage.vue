<script setup>
import '@/domains/agents/ui/agents-ui.css'

import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Menu from 'primevue/menu'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { XCircle } from 'lucide-vue-next'

import UiConfirmModal from '@/shared/ui/UiConfirmModal.vue'
import { formatEnrolledAt } from '@/domains/agents/agents.utils'
import { useAgentsPage } from '@/domains/agents/useAgentsPage'
import AgentsFiltersSection from '@/domains/agents/ui/sections/AgentsFiltersSection.vue'
import AgentsGroupsSection from '@/domains/agents/ui/sections/AgentsGroupsSection.vue'
import AgentsHeaderSection from '@/domains/agents/ui/sections/AgentsHeaderSection.vue'
import AgentsSummarySection from '@/domains/agents/ui/sections/AgentsSummarySection.vue'

const {
  AGENT_OS_OPTIONS,
  AGENT_STATUS_OPTIONS,
  actionsMenu,
  agentToDelete,
  agentToRegenerateToken,
  agentsStore,
  canWriteAgents,
  cardMenuItems,
  clearCreateError,
  clearEditError,
  closeCreateDialog,
  closeDeleteModal,
  closeEditDialog,
  closeRegenerateTokenModal,
  closeTokenDialog,
  copyEnrollmentToken,
  createErrors,
  createForm,
  createSubmitting,
  createVisible,
  deleteModal,
  editErrors,
  editForm,
  editSubmitting,
  editVisible,
  filteredAgents,
  filterState,
  filtersSection,
  getPendingAgentAction,
  getPendingAgentActionLabel,
  groupedAgents,
  handleDelete,
  handleRegenerateEnrollmentToken,
  handleSummaryChipClick,
  initialLoadFinished,
  isAgentBusy,
  isEditUnchanged,
  isGroupCollapsed,
  isSummaryChipActive,
  onOpenActionsMenu,
  onOpenCreate,
  onOpenEdit,
  onPageChange,
  onResetFilters,
  regenerateTokenModal,
  setGroupRef,
  submitCreate,
  submitEdit,
  summaryItems,
  toggleGroup,
  tokenCopied,
  tokenState,
  tokenVisible,
  confirmRegenerateEnrollmentToken,
} = useAgentsPage()
</script>

<template>
  <div class="agents-page">
    <AgentsHeaderSection :can-write-agents="canWriteAgents" :on-open-create="onOpenCreate" />

    <AgentsFiltersSection
      :container-ref="filtersSection"
      :filter-state="filterState"
      :status-options="AGENT_STATUS_OPTIONS"
      :os-options="AGENT_OS_OPTIONS"
      :is-loading="agentsStore.isLoading"
      :on-reset-filters="onResetFilters"
    />

    <AgentsSummarySection
      :items="summaryItems"
      variant="top"
      :is-chip-active="isSummaryChipActive"
      :on-chip-click="handleSummaryChipClick"
    />

    <div class="agents-content">
      <AgentsGroupsSection
        :initial-load-finished="initialLoadFinished"
        :is-loading="agentsStore.isLoading"
        :has-items="Boolean(filteredAgents.length)"
        :has-source-items="Boolean(agentsStore.items.length)"
        :grouped-agents="groupedAgents"
        :can-write-agents="canWriteAgents"
        :limit="agentsStore.limit"
        :total="agentsStore.total"
        :offset="agentsStore.offset"
        :error="agentsStore.error"
        :is-group-collapsed="isGroupCollapsed"
        :on-toggle-group="toggleGroup"
        :set-group-ref="setGroupRef"
        :is-agent-busy="isAgentBusy"
        :get-pending-agent-action-label="getPendingAgentActionLabel"
        :get-pending-agent-action="getPendingAgentAction"
        :on-edit="onOpenEdit"
        :on-token="confirmRegenerateEnrollmentToken"
        :on-menu="onOpenActionsMenu"
        :on-page-change="onPageChange"
        :on-open-create="onOpenCreate"
      />
    </div>

    <Dialog
      v-model:visible="createVisible"
      class="agent-form-dialog"
      modal
      :closable="false"
      :style="{ width: '520px', maxWidth: 'calc(100vw - 32px)' }"
    >
      <template #header>
        <div class="agent-dialog-header">
          <div class="agent-dialog-header__copy">
            <h2 class="agent-dialog-title">Новый агент</h2>
            <p class="agent-dialog-subtitle">Создание записи и выпуск enrollment token для установки.</p>
          </div>
          <button type="button" class="dialog-close-button" aria-label="Закрыть" :disabled="createSubmitting" @click="closeCreateDialog">
            <XCircle :size="18" />
          </button>
        </div>
      </template>

      <div class="dialog-body">
        <div class="dialog-panel">
          <div class="field">
            <label class="field-label" for="agent-create-hostname">Hostname</label>
            <InputText
              id="agent-create-hostname"
              v-model="createForm.hostname"
              :invalid="!!createErrors.hostname"
              placeholder="srv-app-01"
              fluid
              autofocus
              @update:model-value="clearCreateError('hostname')"
            />
            <small v-if="createErrors.hostname" class="field-error">{{ createErrors.hostname }}</small>
          </div>

          <div class="field">
            <label class="field-label" for="agent-create-os">OS</label>
            <Select
              id="agent-create-os"
              v-model="createForm.os"
              :options="AGENT_OS_OPTIONS"
              option-label="label"
              option-value="value"
              :invalid="!!createErrors.os"
              fluid
              @update:model-value="clearCreateError('os')"
            />
            <small v-if="createErrors.os" class="field-error">{{ createErrors.os }}</small>
          </div>
        </div>

        <div class="dialog-panel">
          <div class="field">
            <label class="field-label" for="agent-create-notes">Заметки</label>
            <Textarea
              id="agent-create-notes"
              v-model="createForm.notes"
              rows="4"
              auto-resize
              :invalid="!!createErrors.notes"
              placeholder="Дополнительный контекст по агенту"
              fluid
              @update:model-value="clearCreateError('notes')"
            />
            <small v-if="createErrors.notes" class="field-error">{{ createErrors.notes }}</small>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <Button label="Отмена" severity="secondary" outlined :disabled="createSubmitting" @click="closeCreateDialog" />
          <Button label="Создать" :loading="createSubmitting" :disabled="createSubmitting" @click="submitCreate" />
        </div>
      </template>
    </Dialog>

    <Dialog
      v-model:visible="editVisible"
      class="agent-form-dialog"
      modal
      :closable="false"
      :style="{ width: '520px', maxWidth: 'calc(100vw - 32px)' }"
    >
      <template #header>
        <div class="agent-dialog-header">
          <div class="agent-dialog-header__copy">
            <h2 class="agent-dialog-title">Редактировать агента</h2>
            <p class="agent-dialog-subtitle">Обновление hostname, статуса и операционных заметок.</p>
          </div>
          <button type="button" class="dialog-close-button" aria-label="Закрыть" :disabled="editSubmitting" @click="closeEditDialog">
            <XCircle :size="18" />
          </button>
        </div>
      </template>

      <div class="dialog-body">
        <div class="dialog-panel">
          <div class="field">
            <label class="field-label" for="agent-edit-hostname">Hostname</label>
            <InputText
              id="agent-edit-hostname"
              v-model="editForm.hostname"
              :invalid="!!editErrors.hostname"
              placeholder="srv-app-01"
              fluid
              @update:model-value="clearEditError('hostname')"
            />
            <small v-if="editErrors.hostname" class="field-error">{{ editErrors.hostname }}</small>
          </div>
        </div>

        <div class="dialog-panel">
          <div class="field">
            <label class="field-label" for="agent-edit-status">Статус</label>
            <div id="agent-edit-status" class="status-segmented" :class="{ 'is-invalid': !!editErrors.status }">
              <button
                v-for="option in AGENT_STATUS_OPTIONS"
                :key="option.value"
                type="button"
                class="status-segmented__option"
                :class="{ 'is-active': editForm.status === option.value }"
                @click="editForm.status = option.value; clearEditError('status')"
              >
                {{ option.label }}
              </button>
            </div>
            <small v-if="editErrors.status" class="field-error">{{ editErrors.status }}</small>
          </div>
        </div>

        <div class="dialog-panel">
          <div class="field">
            <label class="field-label" for="agent-edit-notes">Заметки</label>
            <Textarea
              id="agent-edit-notes"
              v-model="editForm.notes"
              rows="4"
              auto-resize
              :invalid="!!editErrors.notes"
              placeholder="Дополнительный контекст по агенту"
              fluid
              @update:model-value="clearEditError('notes')"
            />
            <small v-if="editErrors.notes" class="field-error">{{ editErrors.notes }}</small>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <Button label="Отмена" severity="secondary" outlined :disabled="editSubmitting" @click="closeEditDialog" />
          <Button label="Сохранить" :loading="editSubmitting" :disabled="editSubmitting || isEditUnchanged" @click="submitEdit" />
        </div>
      </template>
    </Dialog>

    <Dialog
      v-model:visible="tokenVisible"
      class="agent-form-dialog agent-token-dialog"
      modal
      :closable="false"
      :style="{ width: '560px', maxWidth: 'calc(100vw - 32px)' }"
    >
      <template #header>
        <div class="agent-dialog-header">
          <div class="agent-dialog-header__copy">
            <h2 class="agent-dialog-title">Enrollment token</h2>
            <p class="agent-dialog-subtitle">Конфигурация для установки агента и одноразовый токен регистрации.</p>
          </div>
          <button type="button" class="dialog-close-button" aria-label="Закрыть" @click="closeTokenDialog">
            <XCircle :size="16" />
          </button>
        </div>
      </template>

      <div v-if="tokenState" class="token-dialog">
        <div class="token-banner">
          <span class="token-banner__title">Токен показывается только один раз</span>
          <span class="token-banner__text">Сохраните его в безопасном месте. После закрытия диалога значение больше не будет доступно.</span>
        </div>

        <section class="token-shell">
          <div class="token-shell__top">
            <div class="token-shell__copy">
              <span class="token-block__label">Enrollment token</span>
              <p class="token-shell__hint">Используйте этот токен при установке или повторной регистрации агента.</p>
            </div>
            <Button
              :label="tokenCopied ? 'Скопировано' : 'Скопировать'"
              severity="secondary"
              outlined
              size="small"
              @click="copyEnrollmentToken"
            />
          </div>

          <div class="token-block">
            <code class="token-block__value">{{ tokenState.enrollment_token }}</code>
          </div>

          <div class="token-meta">
            <div class="token-meta__item">
              <span class="token-meta__label">Hostname</span>
              <strong class="token-meta__value">{{ tokenState.agent.hostname }}</strong>
            </div>
            <div class="token-meta__item">
              <span class="token-meta__label">Истекает</span>
              <strong class="token-meta__value">{{ formatEnrolledAt(tokenState.enrollment_token_expires_at) }}</strong>
            </div>
          </div>
        </section>
      </div>

      <template #footer>
        <Button label="Закрыть" @click="closeTokenDialog" />
      </template>
    </Dialog>

    <UiConfirmModal
      ref="deleteModal"
      title="Удаление агента"
      confirm-text="Удалить"
      cancel-text="Отмена"
      confirm-variant="error"
      busy-text="Удаление..."
      :message="agentToDelete ? `Удалить агента ${agentToDelete.hostname}? Это действие необратимо.` : ''"
      :action="handleDelete"
      @close="closeDeleteModal"
    />

    <UiConfirmModal
      ref="regenerateTokenModal"
      title="Перевыпуск токена"
      confirm-text="Выпустить токен"
      cancel-text="Отмена"
      confirm-variant="warning"
      busy-text="Выпускаем..."
      :message="agentToRegenerateToken ? `Выпустить новый enrollment token для ${agentToRegenerateToken.hostname}? Предыдущий токен станет недействительным.` : ''"
      :action="handleRegenerateEnrollmentToken"
      @close="closeRegenerateTokenModal"
    />

    <Menu ref="actionsMenu" :model="cardMenuItems" popup />
  </div>
</template>
