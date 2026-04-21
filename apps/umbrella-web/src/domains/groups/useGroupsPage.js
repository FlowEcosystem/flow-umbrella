import { computed, onMounted, reactive, ref } from 'vue'
import { useToast } from 'primevue/usetoast'

import { can } from '@/app/access/rbac'
import { useAuthStore } from '@/domains/auth/store'
import { agentsApi } from '@/domains/agents/api'
import { groupsApi } from '@/domains/groups/api'
import { useGroupsStore } from '@/domains/groups/store'
import { buildValidationState } from '@/shared/lib/domain-ui'
import { buildGroupPatch, buildGroupPayload } from '@/domains/groups/groups.utils'

export function useGroupsPage() {
  const authStore = useAuthStore()
  const groupsStore = useGroupsStore()
  const toast = useToast()

  const currentUser = computed(() => authStore.currentUser)
  const canWriteGroups = computed(() => can(currentUser.value?.role, 'groups:write'))

  const initialLoadFinished = ref(false)
  const createVisible = ref(false)
  const editVisible = ref(false)
  const membersVisible = ref(false)
  const deleteModal = ref(null)
  const groupToDelete = ref(null)
  const groupToEdit = ref(null)
  const activeGroup = ref(null)
  const createSubmitting = ref(false)
  const editSubmitting = ref(false)
  const membersLoading = ref(false)
  const membersOffset = ref(0)
  const membersLimit = ref(50)
  const membersTotal = ref(0)
  const groupAgents = ref([])
  const candidateAgents = ref([])
  const candidateSearch = ref('')
  const candidateLoading = ref(false)
  const selectedAgentIds = ref([])
  const addAgentsSubmitting = ref(false)
  const removingAgentId = ref(null)

  const createForm = reactive({
    name: '',
    description: '',
    color: '#c17f59',
  })

  const editForm = reactive({
    name: '',
    description: '',
    color: '#c17f59',
  })

  const createErrors = reactive({
    name: '',
    description: '',
    color: '',
  })

  const editErrors = reactive({
    name: '',
    description: '',
    color: '',
  })

  const editInitial = reactive({
    name: '',
    description: null,
    color: null,
  })

  const isEditUnchanged = computed(() => {
    if (!groupToEdit.value) return true
    return Object.keys(buildGroupPatch(editForm, editInitial)).length === 0
  })

  async function loadGroups(params = {}) {
    try {
      await groupsStore.fetch(params)
    } catch (err) {
      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4000 })
    } finally {
      initialLoadFinished.value = true
    }
  }

  function handlePageChange(event) {
    loadGroups({ limit: event.rows, offset: event.first })
  }

  function resetCreateForm() {
    createForm.name = ''
    createForm.description = ''
    createForm.color = '#c17f59'
    Object.assign(createErrors, { name: '', description: '', color: '' })
  }

  function openCreate() {
    resetCreateForm()
    createVisible.value = true
  }

  async function submitCreate() {
    if (createSubmitting.value) return

    createSubmitting.value = true
    Object.assign(createErrors, { name: '', description: '', color: '' })
    try {
      await groupsStore.create(buildGroupPayload(createForm))
      createVisible.value = false
      toast.add({ severity: 'success', summary: 'Группа создана', life: 3000 })
    } catch (err) {
      if (err.status === 409 && err.error_code === 'group_name_already_exists') {
        createErrors.name = 'Группа с таким именем уже существует'
        return
      }

      if (err.status === 422) {
        Object.assign(createErrors, buildValidationState(err, ['name', 'description', 'color']))
        return
      }

      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      createSubmitting.value = false
    }
  }

  function openEdit(group) {
    groupToEdit.value = group
    editForm.name = group.name
    editForm.description = group.description ?? ''
    editForm.color = group.color ?? '#c17f59'
    editInitial.name = group.name
    editInitial.description = group.description
    editInitial.color = group.color
    Object.assign(editErrors, { name: '', description: '', color: '' })
    editVisible.value = true
  }

  async function submitEdit() {
    if (editSubmitting.value || isEditUnchanged.value || !groupToEdit.value) return

    editSubmitting.value = true
    Object.assign(editErrors, { name: '', description: '', color: '' })
    try {
      await groupsStore.update(groupToEdit.value.id, buildGroupPatch(editForm, editInitial))
      editVisible.value = false
      groupToEdit.value = null
      toast.add({ severity: 'success', summary: 'Изменения сохранены', life: 3000 })
    } catch (err) {
      if (err.status === 409 && err.error_code === 'group_name_already_exists') {
        editErrors.name = 'Группа с таким именем уже существует'
        return
      }

      if (err.status === 422) {
        Object.assign(editErrors, buildValidationState(err, ['name', 'description', 'color']))
        return
      }

      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      editSubmitting.value = false
    }
  }

  function confirmDelete(group) {
    groupToDelete.value = group
    deleteModal.value?.open()
  }

  async function handleDelete() {
    if (!groupToDelete.value) return

    const deletingLastVisibleRow = groupsStore.items.length === 1 && groupsStore.offset > 0
    const currentOffset = groupsStore.offset
    const currentLimit = groupsStore.limit

    try {
      await groupsStore.remove(groupToDelete.value.id)
      toast.add({ severity: 'success', summary: 'Группа удалена', life: 3000 })
      if (deletingLastVisibleRow && groupsStore.total > 0) {
        await loadGroups({ limit: currentLimit, offset: Math.max(0, currentOffset - currentLimit) })
      }
      groupToDelete.value = null
    } catch (err) {
      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
      throw err
    }
  }

  async function refreshActiveGroup() {
    if (!activeGroup.value) return
    const fresh = await groupsApi.get(activeGroup.value.id)
    activeGroup.value = fresh
    groupsStore.replaceOne(fresh)
  }

  async function loadGroupAgents() {
    if (!activeGroup.value) return
    membersLoading.value = true
    try {
      const data = await groupsApi.listAgents({
        groupId: activeGroup.value.id,
        limit: membersLimit.value,
        offset: membersOffset.value,
      })
      groupAgents.value = data.items
      membersTotal.value = data.meta.total
    } catch (err) {
      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4000 })
    } finally {
      membersLoading.value = false
    }
  }

  async function searchCandidateAgents() {
    if (!activeGroup.value) return
    candidateLoading.value = true
    try {
      const data = await agentsApi.list({
        limit: 50,
        offset: 0,
        search: candidateSearch.value,
      })
      candidateAgents.value = data.items
    } catch (err) {
      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4000 })
    } finally {
      candidateLoading.value = false
    }
  }

  async function openMembers(group) {
    activeGroup.value = group
    membersOffset.value = 0
    selectedAgentIds.value = []
    candidateSearch.value = ''
    membersVisible.value = true
    await Promise.all([loadGroupAgents(), searchCandidateAgents()])
  }

  function handleMembersPageChange(event) {
    membersOffset.value = event.first
    membersLimit.value = event.rows
    loadGroupAgents()
  }

  async function addAgentsToGroup() {
    if (!activeGroup.value || !selectedAgentIds.value.length || addAgentsSubmitting.value) return

    addAgentsSubmitting.value = true
    try {
      const response = await groupsApi.addAgents(activeGroup.value.id, selectedAgentIds.value)
      selectedAgentIds.value = []
      await Promise.all([refreshActiveGroup(), loadGroupAgents(), searchCandidateAgents()])
      const summary = response.already_in_group
        ? `Добавлено: ${response.added}, уже состояли: ${response.already_in_group}`
        : `Добавлено агентов: ${response.added}`
      toast.add({ severity: 'success', summary, life: 3500 })
    } catch (err) {
      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      addAgentsSubmitting.value = false
    }
  }

  async function removeAgentFromGroup(agent) {
    if (!activeGroup.value || removingAgentId.value) return

    removingAgentId.value = agent.id
    try {
      await groupsApi.removeAgent(activeGroup.value.id, agent.id)
      await Promise.all([refreshActiveGroup(), loadGroupAgents(), searchCandidateAgents()])
      toast.add({ severity: 'success', summary: 'Агент убран из группы', life: 3000 })
    } catch (err) {
      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      removingAgentId.value = null
    }
  }

  function clearCreateError(field) {
    createErrors[field] = ''
  }

  function clearEditError(field) {
    editErrors[field] = ''
  }

  function closeDeleteModal() {
    groupToDelete.value = null
  }

  onMounted(() => {
    loadGroups({ limit: groupsStore.limit, offset: groupsStore.offset })
  })

  return {
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
    groupToEdit,
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
    onOpenCreate: openCreate,
    onOpenEdit: openEdit,
    onOpenMembers: openMembers,
    onConfirmDelete: confirmDelete,
    removeAgentFromGroup,
    removingAgentId,
    searchCandidateAgents,
    selectedAgentIds,
    submitCreate,
    submitEdit,
    addAgentsToGroup,
  }
}
