import { useGroupsStore }  from '@/domains/groups/store'
import { useAgentsStore }  from '@/domains/agents/store'
import { useToast }        from '@/shared/composables/useToast'
import { usePagination }   from '@/shared/composables/usePagination'
import { groupsApi }       from '@/domains/groups/api'
import { COLOR_PRESETS }   from '@/domains/groups/groups.utils'

export function useGroupsPage() {
  const store       = useGroupsStore()
  const agentsStore = useAgentsStore()
  const toast       = useToast()

  onMounted(() => {
    store.fetch()
    if (!agentsStore.items.length) agentsStore.fetch()
  })

  // ── local filter ─────────────────────────────────────────
  const searchQuery = ref('')

  const filteredGroups = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return store.items
    return store.items.filter(g =>
      g.name.toLowerCase().includes(q) ||
      (g.description ?? '').toLowerCase().includes(q)
    )
  })

  const hasFilters = computed(() => !!searchQuery.value.trim())

  function resetFilters() { searchQuery.value = '' }

  const { page, totalPages, paged: pagedGroups, goTo } = usePagination(filteredGroups, 24)

  // ── form dialog (create + edit) ───────────────────────────
  const formOpen    = ref(false)
  const formTarget  = ref(null)  // null = create, object = edit
  const formData    = ref({ name: '', description: '', color: '' })
  const formLoading = ref(false)
  const formError   = ref('')

  function openCreate() {
    formTarget.value  = null
    formData.value    = { name: '', description: '', color: COLOR_PRESETS[0] }
    formError.value   = ''
    formOpen.value    = true
  }

  function openEdit(group) {
    formTarget.value  = group
    formData.value    = { name: group.name, description: group.description ?? '', color: group.color ?? '' }
    formError.value   = ''
    formOpen.value    = true
  }

  async function submitForm() {
    formLoading.value = true
    formError.value   = ''
    try {
      const payload = {
        name:        formData.value.name,
        description: formData.value.description || null,
        color:       formData.value.color || null,
      }
      if (formTarget.value) {
        await store.update(formTarget.value.id, payload)
        toast.success('Группа обновлена')
      } else {
        await store.create(payload)
        toast.success('Группа создана')
      }
      formOpen.value = false
    } catch (err) {
      formError.value = err.message ?? 'Ошибка сохранения'
    } finally {
      formLoading.value = false
    }
  }

  // ── delete ───────────────────────────────────────────────
  const deleteTarget  = ref(null)
  const deleteLoading = ref(false)

  function openDelete(group)  { deleteTarget.value = group }
  function closeDelete()      { deleteTarget.value = null  }

  async function confirmDelete() {
    if (!deleteTarget.value) return
    deleteLoading.value = true
    try {
      await store.remove(deleteTarget.value.id)
      toast.success('Группа удалена')
      deleteTarget.value = null
    } catch (err) {
      toast.error(err.message ?? 'Ошибка удаления')
      deleteTarget.value = null
    } finally {
      deleteLoading.value = false
    }
  }

  // ── members dialog ────────────────────────────────────────
  const membersOpen    = ref(false)
  const membersTarget  = ref(null)
  const membersList    = ref([])
  const membersLoading = ref(false)
  const membersError   = ref('')
  const addLoading     = ref(false)
  const removeLoading  = ref({})  // { [agentId]: bool }

  async function openMembers(group) {
    membersTarget.value = group
    membersError.value  = ''
    membersList.value   = []
    membersOpen.value   = true
    await fetchMembers()
  }

  async function fetchMembers() {
    if (!membersTarget.value) return
    membersLoading.value = true
    try {
      const data = await groupsApi.listAgents(membersTarget.value.id)
      membersList.value = data.items ?? data
    } catch (err) {
      membersError.value = err.message ?? 'Ошибка загрузки'
    } finally {
      membersLoading.value = false
    }
  }

  const memberIds = computed(() => new Set(membersList.value.map(a => a.id)))

  const availableAgents = computed(() =>
    agentsStore.items.filter(a => !memberIds.value.has(a.id))
  )

  async function addAgent(agentId) {
    if (!membersTarget.value) return
    addLoading.value = true
    try {
      await groupsApi.addAgents(membersTarget.value.id, [agentId])
      const agent = agentsStore.items.find(a => a.id === agentId)
      if (agent) membersList.value.push(agent)
      store.patchCount(membersTarget.value.id, +1)
    } catch { /* ignore */ } finally {
      addLoading.value = false
    }
  }

  async function removeAgent(agentId) {
    if (!membersTarget.value) return
    removeLoading.value = { ...removeLoading.value, [agentId]: true }
    try {
      await groupsApi.removeAgent(membersTarget.value.id, agentId)
      membersList.value = membersList.value.filter(a => a.id !== agentId)
      store.patchCount(membersTarget.value.id, -1)
    } catch { /* ignore */ } finally {
      const next = { ...removeLoading.value }
      delete next[agentId]
      removeLoading.value = next
    }
  }

  return {
    store,
    filteredGroups, pagedGroups, page, totalPages, goTo,
    searchQuery, hasFilters, resetFilters,
    formOpen, formTarget, formData, formLoading, formError,
    openCreate, openEdit, submitForm,
    deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
    membersOpen, membersTarget, membersList, membersLoading, membersError,
    addLoading, removeLoading,
    availableAgents, memberIds,
    openMembers, addAgent, removeAgent,
    COLOR_PRESETS,
  }
}
