<script setup>
import '@/domains/admins/ui/admins-ui.css'

import UiConfirmModal from '@/shared/ui/UiConfirmModal.vue'
import AdminCreateModal from '@/domains/admins/ui/components/AdminCreateModal.vue'
import AdminEditModal from '@/domains/admins/ui/components/AdminEditModal.vue'
import { useAdminsPage } from '@/domains/admins/useAdminsPage'
import AdminsHeaderSection from '@/domains/admins/ui/sections/AdminsHeaderSection.vue'
import AdminsTableSection from '@/domains/admins/ui/sections/AdminsTableSection.vue'

const {
  adminsStore,
  adminToDelete,
  adminToEdit,
  avatarLabel,
  canManageAdmins,
  confirmDelete,
  createVisible,
  currentUser,
  deleteModal,
  editVisible,
  formatRelativeLastLogin,
  handleCreated,
  handleDelete,
  handlePageChange,
  initialLoadFinished,
  isCurrentUser,
  onDeleteModalClose,
  onOpenCreate,
  onOpenEdit,
  submitEdit,
} = useAdminsPage()
</script>

<template>
  <div class="admins-page">
    <AdminsHeaderSection :can-manage-admins="canManageAdmins" :on-open-create="onOpenCreate" />

    <AdminsTableSection
      :admins-store="adminsStore"
      :initial-load-finished="initialLoadFinished"
      :can-manage-admins="canManageAdmins"
      :is-current-user="isCurrentUser"
      :avatar-label="avatarLabel"
      :format-relative-last-login="formatRelativeLastLogin"
      :on-open-edit="onOpenEdit"
      :on-confirm-delete="confirmDelete"
      :on-open-create="onOpenCreate"
      :on-page-change="handlePageChange"
    />

    <AdminCreateModal v-model:visible="createVisible" @created="handleCreated" />

    <AdminEditModal
      v-model:visible="editVisible"
      :admin="adminToEdit"
      :on-submit="submitEdit"
      :current-user-id="currentUser?.id"
    />

    <UiConfirmModal
      ref="deleteModal"
      title="Удаление администратора"
      confirm-text="Удалить"
      cancel-text="Отмена"
      confirm-variant="error"
      busy-text="Удаление..."
      :message="adminToDelete ? `Удалить администратора ${adminToDelete.email}? Это действие необратимо.` : ''"
      :action="handleDelete"
      @close="onDeleteModalClose"
    />
  </div>
</template>
