import { computed, onMounted, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'

import { can } from '@/app/access/rbac'
import { useAuthStore } from '@/domains/auth/store'
import { useAdminsStore } from '@/domains/admins/store'
import { formatLastLogin, getAdminInitials } from '@/domains/admins/admins.utils'

export function useAdminsPage() {
  const authStore = useAuthStore()
  const adminsStore = useAdminsStore()
  const toast = useToast()

  const createVisible = ref(false)
  const editVisible = ref(false)
  const adminToEdit = ref(null)
  const adminToDelete = ref(null)
  const initialLoadFinished = ref(false)
  const deleteModal = ref(null)

  const currentUser = computed(() => authStore.currentUser)
  const canManageAdmins = computed(() => can(currentUser.value?.role, 'admins:write'))

  async function loadAdmins(params = {}) {
    try {
      await adminsStore.fetch(params)
    } catch (err) {
      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4000 })
    } finally {
      initialLoadFinished.value = true
    }
  }

  async function handlePageChange(event) {
    await loadAdmins({ limit: event.rows, offset: event.first })
  }

  function handleCreated() {
    initialLoadFinished.value = true
  }

  function openCreate() {
    createVisible.value = true
  }

  function openEdit(admin) {
    adminToEdit.value = admin
    editVisible.value = true
  }

  async function submitEdit(id, patch) {
    return adminsStore.update(id, patch)
  }

  async function handleDelete() {
    if (!adminToDelete.value) return

    const deletingLastVisibleRow = adminsStore.items.length === 1 && adminsStore.offset > 0
    const currentOffset = adminsStore.offset
    const currentLimit = adminsStore.limit

    try {
      await adminsStore.remove(adminToDelete.value.id)
      toast.add({ severity: 'success', summary: 'Администратор удалён', life: 3000 })

      if (deletingLastVisibleRow && adminsStore.total > 0) {
        const prevOffset = Math.max(0, currentOffset - currentLimit)
        await loadAdmins({ limit: currentLimit, offset: prevOffset })
      }

      adminToDelete.value = null
    } catch (err) {
      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
      throw err
    }
  }

  function confirmDelete(admin) {
    adminToDelete.value = admin
    deleteModal.value?.open()
  }

  function isCurrentUser(admin) {
    return admin.id === currentUser.value?.id
  }

  function avatarLabel(admin) {
    return getAdminInitials(admin) || '?'
  }

  function onDeleteModalClose() {
    adminToDelete.value = null
  }

  watch(editVisible, (value) => {
    if (!value) adminToEdit.value = null
  })

  onMounted(() => {
    loadAdmins({ limit: adminsStore.limit, offset: adminsStore.offset })
  })

  return {
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
    formatRelativeLastLogin: formatLastLogin,
    handleCreated,
    handleDelete,
    handlePageChange,
    initialLoadFinished,
    isCurrentUser,
    onDeleteModalClose,
    onOpenCreate: openCreate,
    onOpenEdit: openEdit,
    submitEdit,
  }
}
