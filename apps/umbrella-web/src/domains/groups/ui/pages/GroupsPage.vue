<script setup>
import '@/domains/groups/ui/groups-ui.css'

import UiConfirmModal from '@/shared/ui/UiConfirmModal.vue'
import { useGroupsPage } from '@/domains/groups/useGroupsPage'
import GroupFormDialog from '@/domains/groups/ui/components/GroupFormDialog.vue'
import GroupMembersDialog from '@/domains/groups/ui/components/GroupMembersDialog.vue'
import GroupsHeaderSection from '@/domains/groups/ui/sections/GroupsHeaderSection.vue'
import GroupsTableSection from '@/domains/groups/ui/sections/GroupsTableSection.vue'

const {
  activeGroup,
  addAgentsSubmitting,
  candidateAgents,
  candidateLoading,
  candidateSearch,
  canWriteGroups,
  clearCreateError,
  clearEditError,
  closeDeleteModal,
  createErrors,
  createForm,
  createSubmitting,
  createVisible,
  deleteModal,
  editErrors,
  editForm,
  editSubmitting,
  editVisible,
  groupAgents,
  groupToDelete,
  groupsStore,
  handleDelete,
  handleMembersPageChange,
  handlePageChange,
  initialLoadFinished,
  isEditUnchanged,
  membersLimit,
  membersLoading,
  membersOffset,
  membersTotal,
  membersVisible,
  onConfirmDelete,
  onOpenCreate,
  onOpenEdit,
  onOpenMembers,
  removeAgentFromGroup,
  removingAgentId,
  searchCandidateAgents,
  selectedAgentIds,
  submitCreate,
  submitEdit,
  addAgentsToGroup,
} = useGroupsPage()
</script>

<template>
  <div class="groups-page">
    <GroupsHeaderSection :can-write-groups="canWriteGroups" :on-open-create="onOpenCreate" />

    <GroupsTableSection
      :groups-store="groupsStore"
      :initial-load-finished="initialLoadFinished"
      :can-write-groups="canWriteGroups"
      :on-open-create="onOpenCreate"
      :on-open-edit="onOpenEdit"
      :on-open-members="onOpenMembers"
      :on-confirm-delete="onConfirmDelete"
      :on-page-change="handlePageChange"
    />

    <GroupFormDialog
      v-model:visible="createVisible"
      mode="create"
      :form="createForm"
      :errors="createErrors"
      :is-submitting="createSubmitting"
      :on-submit="submitCreate"
      :on-clear-error="clearCreateError"
    />

    <GroupFormDialog
      v-model:visible="editVisible"
      mode="edit"
      :form="editForm"
      :errors="editErrors"
      :is-submitting="editSubmitting"
      :is-unchanged="isEditUnchanged"
      :on-submit="submitEdit"
      :on-clear-error="clearEditError"
    />

    <GroupMembersDialog
      v-model:visible="membersVisible"
      v-model:candidate-search="candidateSearch"
      v-model:selected-agent-ids="selectedAgentIds"
      :active-group="activeGroup"
      :can-write-groups="canWriteGroups"
      :members-loading="membersLoading"
      :members-offset="membersOffset"
      :members-limit="membersLimit"
      :members-total="membersTotal"
      :group-agents="groupAgents"
      :candidate-agents="candidateAgents"
      :candidate-search="candidateSearch"
      :candidate-loading="candidateLoading"
      :selected-agent-ids="selectedAgentIds"
      :add-agents-submitting="addAgentsSubmitting"
      :removing-agent-id="removingAgentId"
      :on-search-candidate-agents="searchCandidateAgents"
      :on-handle-members-page-change="handleMembersPageChange"
      :on-add-agents-to-group="addAgentsToGroup"
      :on-remove-agent-from-group="removeAgentFromGroup"
    />

    <UiConfirmModal
      ref="deleteModal"
      title="Удаление группы"
      confirm-text="Удалить"
      cancel-text="Отмена"
      confirm-variant="error"
      busy-text="Удаление..."
      :message="groupToDelete ? `Удалить группу ${groupToDelete.name}? Это действие необратимо.` : ''"
      :action="handleDelete"
      @close="closeDeleteModal"
    />
  </div>
</template>
