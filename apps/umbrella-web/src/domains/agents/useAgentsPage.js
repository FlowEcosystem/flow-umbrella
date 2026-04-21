import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'

import { can } from '@/app/access/rbac'
import { useAuthStore } from '@/domains/auth/store'
import { useAgentsStore } from '@/domains/agents/store'
import { buildValidationState } from '@/shared/lib/domain-ui'
import {
  AGENT_OS_OPTIONS,
  AGENT_STATUS_OPTIONS,
  buildAgentCreatePayload,
  buildAgentPatch,
} from '@/domains/agents/agents.utils'

export function useAgentsPage() {
  const authStore = useAuthStore()
  const agentsStore = useAgentsStore()
  const toast = useToast()

  const currentUser = computed(() => authStore.currentUser)
  const canWriteAgents = computed(() => can(currentUser.value?.role, 'agents:write'))

  const filterState = reactive({
    search: agentsStore.filters.search ?? '',
    status: agentsStore.filters.status ?? [],
    os: agentsStore.filters.os ?? null,
  })

  const initialLoadFinished = ref(false)
  const createVisible = ref(false)
  const editVisible = ref(false)
  const tokenVisible = ref(false)
  const agentToEdit = ref(null)
  const agentToDelete = ref(null)
  const agentToRegenerateToken = ref(null)
  const deleteModal = ref(null)
  const regenerateTokenModal = ref(null)
  const actionsMenu = ref(null)
  const tokenState = ref(null)
  const tokenCopied = ref(false)
  const createSubmitting = ref(false)
  const editSubmitting = ref(false)
  const menuAgent = ref(null)
  const collapsedGroups = ref({})
  const groupRefs = ref({})
  const pendingAgentActions = reactive({})
  const filtersSection = ref(null)
  let filterApplyTimer = 0
  let suppressFilterWatch = false

  const createForm = reactive({
    hostname: '',
    os: 'linux',
    notes: '',
  })

  const editForm = reactive({
    hostname: '',
    status: 'pending',
    notes: '',
  })

  const createErrors = reactive({
    hostname: '',
    os: '',
    notes: '',
  })

  const editErrors = reactive({
    hostname: '',
    status: '',
    notes: '',
  })

  const editInitial = reactive({
    hostname: '',
    status: 'pending',
    notes: null,
  })

  const isEditUnchanged = computed(() => {
    if (!agentToEdit.value) return true
    return Object.keys(buildAgentPatch(editForm, editInitial)).length === 0
  })

  const statusOrder = Object.freeze(['active', 'pending', 'disabled', 'decommissioned'])

  const filteredAgents = computed(() => {
    const search = filterState.search.trim().toLowerCase()

    return agentsStore.items.filter((agent) => {
      if (filterState.status.length && !filterState.status.includes(agent.status)) {
        return false
      }

      if (filterState.os && agent.os !== filterState.os) {
        return false
      }

      if (search && !agent.hostname.toLowerCase().includes(search)) {
        return false
      }

      return true
    })
  })

  const groupedAgents = computed(() =>
    [...AGENT_STATUS_OPTIONS]
      .sort((a, b) => statusOrder.indexOf(a.value) - statusOrder.indexOf(b.value))
      .map((option) => ({
        key: option.value,
        label: option.label,
        items: filteredAgents.value.filter((agent) => agent.status === option.value),
      }))
      .filter((group) => group.items.length > 0),
  )

  const summaryItems = computed(() =>
    [...AGENT_STATUS_OPTIONS]
      .sort((a, b) => statusOrder.indexOf(a.value) - statusOrder.indexOf(b.value))
      .map((option) => ({
        key: option.value,
        label: option.label,
        count: filteredAgents.value.filter((agent) => agent.status === option.value).length,
      })),
  )

  function setPendingAgentAction(id, action) {
    pendingAgentActions[id] = action
  }

  function clearPendingAgentAction(id) {
    delete pendingAgentActions[id]
  }

  function getPendingAgentAction(id) {
    return pendingAgentActions[id] ?? null
  }

  function isAgentBusy(id) {
    return Boolean(getPendingAgentAction(id))
  }

  function getPendingAgentActionLabel(id) {
    switch (getPendingAgentAction(id)) {
      case 'edit':
        return 'Сохраняем изменения'
      case 'token':
        return 'Готовим токен'
      case 'delete':
        return 'Удаляем агента'
      default:
        return 'Обновляем данные'
    }
  }

  async function loadAgents(params = {}) {
    try {
      await agentsStore.fetch(params)
    } catch (err) {
      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4000 })
    } finally {
      initialLoadFinished.value = true
    }
  }

  function resetFilters() {
    suppressFilterWatch = true
    clearTimeout(filterApplyTimer)
    filterState.search = ''
    filterState.status = []
    filterState.os = null
    agentsStore.filters = { search: '', status: [], os: null }
    suppressFilterWatch = false
  }

  function handlePageChange(event) {
    loadAgents({
      limit: event.rows,
      offset: event.first,
    })
  }

  function isSummaryChipActive(statusKey) {
    return filterState.status.length === 1 && filterState.status[0] === statusKey
  }

  function handleSummaryChipClick(statusKey) {
    const nextStatus = isSummaryChipActive(statusKey) ? [] : [statusKey]
    suppressFilterWatch = true
    clearTimeout(filterApplyTimer)
    filterState.status = nextStatus
    agentsStore.filters = {
      ...agentsStore.filters,
      status: nextStatus,
    }
    suppressFilterWatch = false

    if (nextStatus.length === 1) {
      focusGroup(statusKey)
    }
  }

  function resetCreateForm() {
    createForm.hostname = ''
    createForm.os = 'linux'
    createForm.notes = ''
    Object.assign(createErrors, { hostname: '', os: '', notes: '' })
  }

  function openCreate() {
    resetCreateForm()
    createVisible.value = true
  }

  async function submitCreate() {
    if (createSubmitting.value) return

    createSubmitting.value = true
    Object.assign(createErrors, { hostname: '', os: '', notes: '' })
    try {
      const response = await agentsStore.create(buildAgentCreatePayload(createForm))
      createVisible.value = false
      tokenState.value = response
      tokenVisible.value = true
      toast.add({ severity: 'success', summary: 'Агент создан', life: 3000 })
    } catch (err) {
      if (err.status === 409 && err.error_code === 'agent_hostname_already_exists') {
        createErrors.hostname = 'Hostname уже используется'
        return
      }

      if (err.status === 422) {
        Object.assign(createErrors, buildValidationState(err, ['hostname', 'os', 'notes']))
        return
      }

      toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      createSubmitting.value = false
    }
  }

  function openEdit(agent) {
    agentToEdit.value = agent
    editForm.hostname = agent.hostname
    editForm.status = agent.status
    editForm.notes = agent.notes ?? ''
    editInitial.hostname = agent.hostname
    editInitial.status = agent.status
    editInitial.notes = agent.notes
    Object.assign(editErrors, { hostname: '', status: '', notes: '' })
    editVisible.value = true
  }

  async function submitEdit() {
    if (editSubmitting.value || isEditUnchanged.value || !agentToEdit.value) return

    const agentId = agentToEdit.value.id
    editSubmitting.value = true
    setPendingAgentAction(agentId, 'edit')
    Object.assign(editErrors, { hostname: '', status: '', notes: '' })
    try {
      await agentsStore.update(agentId, buildAgentPatch(editForm, editInitial))
      editVisible.value = false
      agentToEdit.value = null
      toast.add({ severity: 'success', summary: 'Изменения сохранены', life: 3000 })
    } catch (err) {
      if (err.status === 409 && err.error_code === 'agent_hostname_already_exists') {
        editErrors.hostname = 'Hostname уже используется'
        return
      }

      if (err.status === 422) {
        Object.assign(editErrors, buildValidationState(err, ['hostname', 'status', 'notes']))
        return
      }

      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      editSubmitting.value = false
      clearPendingAgentAction(agentId)
    }
  }

  function confirmDelete(agent) {
    agentToDelete.value = agent
    deleteModal.value?.open()
  }

  function confirmRegenerateEnrollmentToken(agent) {
    agentToRegenerateToken.value = agent
    regenerateTokenModal.value?.open()
  }

  function openActionsMenu(event, agent) {
    menuAgent.value = agent
    actionsMenu.value?.toggle(event)
  }

  async function handleDelete() {
    if (!agentToDelete.value) return

    const agentId = agentToDelete.value.id
    const deletingLastVisibleRow = agentsStore.items.length === 1 && agentsStore.offset > 0
    const currentLimit = agentsStore.limit
    const currentOffset = agentsStore.offset

    try {
      setPendingAgentAction(agentId, 'delete')
      await agentsStore.remove(agentId)
      toast.add({ severity: 'success', summary: 'Агент удалён', life: 3000 })
      if (deletingLastVisibleRow && agentsStore.total > 0) {
        await loadAgents({
          limit: currentLimit,
          offset: Math.max(0, currentOffset - currentLimit),
        })
      }
      agentToDelete.value = null
    } catch (err) {
      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
      throw err
    } finally {
      clearPendingAgentAction(agentId)
    }
  }

  async function regenerateEnrollmentToken(agent) {
    try {
      setPendingAgentAction(agent.id, 'token')
      const response = await agentsStore.regenerateEnrollmentToken(agent.id)
      tokenState.value = response
      tokenCopied.value = false
      tokenVisible.value = true
      toast.add({ severity: 'success', summary: 'Новый токен готов', life: 3000 })
    } catch (err) {
      toast.add({ severity: err.status === 409 ? 'warn' : err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4500 })
    } finally {
      clearPendingAgentAction(agent.id)
    }
  }

  function closeDeleteModal() {
    agentToDelete.value = null
  }

  function closeRegenerateTokenModal() {
    agentToRegenerateToken.value = null
  }

  function clearCreateError(field) {
    createErrors[field] = ''
  }

  function clearEditError(field) {
    editErrors[field] = ''
  }

  function toggleGroup(groupKey) {
    collapsedGroups.value = {
      ...collapsedGroups.value,
      [groupKey]: !collapsedGroups.value[groupKey],
    }
  }

  function isGroupCollapsed(groupKey) {
    return Boolean(collapsedGroups.value[groupKey])
  }

  function setGroupRef(groupKey, el) {
    if (el) {
      groupRefs.value[groupKey] = el
    } else {
      delete groupRefs.value[groupKey]
    }
  }

  function focusGroup(groupKey) {
    if (isGroupCollapsed(groupKey)) {
      toggleGroup(groupKey)
    }

    requestAnimationFrame(() => {
      groupRefs.value[groupKey]?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }

  function closeCreateDialog() {
    if (createSubmitting.value) return
    createVisible.value = false
  }

  function closeEditDialog() {
    if (editSubmitting.value) return
    editVisible.value = false
  }

  function closeTokenDialog() {
    tokenVisible.value = false
    tokenCopied.value = false
  }

  async function handleRegenerateEnrollmentToken() {
    if (!agentToRegenerateToken.value) return
    await regenerateEnrollmentToken(agentToRegenerateToken.value)
    agentToRegenerateToken.value = null
  }

  async function copyEnrollmentToken() {
    if (!tokenState?.value?.enrollment_token) return

    try {
      await navigator.clipboard.writeText(tokenState.value.enrollment_token)
      tokenCopied.value = true
      toast.add({ severity: 'success', summary: 'Токен скопирован', life: 2200 })
    } catch {
      toast.add({ severity: 'error', summary: 'Не удалось скопировать токен', life: 3000 })
    }
  }

  const cardMenuItems = computed(() => {
    if (!menuAgent.value) return []

    return [
      {
        label: 'Удалить',
        icon: 'pi pi-trash',
        command: () => confirmDelete(menuAgent.value),
      },
    ]
  })

  onMounted(() => {
    loadAgents({
      limit: agentsStore.limit,
      offset: agentsStore.offset,
    })
  })

  onBeforeUnmount(() => {
    clearTimeout(filterApplyTimer)
  })

  watch(
    () => filterState.search,
    (value) => {
      if (suppressFilterWatch) return
      clearTimeout(filterApplyTimer)
      filterApplyTimer = window.setTimeout(() => {
        agentsStore.filters = {
          ...agentsStore.filters,
          search: value,
        }
      }, 120)
    },
    { flush: 'sync' },
  )

  watch(
    () => filterState.os,
    (value) => {
      if (suppressFilterWatch) return
      clearTimeout(filterApplyTimer)
      agentsStore.filters = {
        ...agentsStore.filters,
        os: value,
      }
    },
    { flush: 'sync' },
  )

  watch(
    () => [...filterState.status],
    (value) => {
      if (suppressFilterWatch) return
      clearTimeout(filterApplyTimer)
      agentsStore.filters = {
        ...agentsStore.filters,
        status: value,
      }
    },
    { flush: 'sync' },
  )

  return {
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
    confirmDelete,
    confirmRegenerateEnrollmentToken,
    copyEnrollmentToken,
    createErrors,
    createForm,
    createSubmitting,
    createVisible,
    currentUser,
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
    handlePageChange,
    handleRegenerateEnrollmentToken,
    handleSummaryChipClick,
    initialLoadFinished,
    isAgentBusy,
    isEditUnchanged,
    isGroupCollapsed,
    isSummaryChipActive,
    menuAgent,
    onOpenActionsMenu: openActionsMenu,
    onOpenCreate: openCreate,
    onOpenEdit: openEdit,
    onPageChange: handlePageChange,
    onResetFilters: resetFilters,
    regenerateTokenModal,
    setGroupRef,
    submitCreate,
    submitEdit,
    summaryItems,
    toggleGroup,
    tokenCopied,
    tokenState,
    tokenVisible,
  }
}
