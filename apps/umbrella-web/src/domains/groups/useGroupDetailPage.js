import { useGroupsStore }  from '@/domains/groups/store'
import { useAgentsStore }  from '@/domains/agents/store'
import { useToast }        from '@/shared/composables/useToast'
import { groupsApi }       from '@/domains/groups/api'
import { policiesApi }     from '@/domains/policies/api'
import { colorDotStyle, fallbackColor } from '@/domains/groups/groups.utils'
import { STATUS_DOT, formatLastSeen }   from '@/domains/agents/agents.utils'

export function useGroupDetailPage(id) {
  const groupsStore = useGroupsStore()
  const agentsStore = useAgentsStore()
  const toast       = useToast()
  const router      = useRouter()

  const group = computed(() => groupsStore.items.find(g => g.id === id))

  const isLoading  = ref(false)
  const localGroup = ref(null)

  const displayGroup = computed(() => localGroup.value ?? group.value ?? null)

  // ── members ────────────────────────────────────────────────
  const members        = ref([])
  const membersLoading = ref(false)

  // ── policies ───────────────────────────────────────────────
  const policies        = ref([])
  const policiesLoading = ref(false)

  async function fetchPolicies() {
    policiesLoading.value = true
    try {
      policies.value = await groupsApi.listPolicies(id)
    } catch {
      policies.value = []
    } finally {
      policiesLoading.value = false
    }
  }

  // ── assign policy ──────────────────────────────────────────
  const assignOpen           = ref(false)
  const assignSearch         = ref('')
  const assignLoading        = ref(false)
  const allPolicies          = ref([])
  const allPoliciesLoading   = ref(false)
  const togglingPolicyId     = ref(null)

  const assignedPolicyIds = computed(() => new Set(policies.value.map(p => p.id)))

  const availablePolicies = computed(() => {
    const q = assignSearch.value.trim().toLowerCase()
    return allPolicies.value.filter(p =>
      !assignedPolicyIds.value.has(p.id) &&
      (!q || p.name.toLowerCase().includes(q))
    )
  })

  async function openAssign() {
    assignOpen.value  = true
    assignSearch.value = ''
    if (!allPolicies.value.length) {
      allPoliciesLoading.value = true
      try {
        const data = await policiesApi.list({ limit: 200 })
        allPolicies.value = data.items ?? data
      } catch {
        allPolicies.value = []
      } finally {
        allPoliciesLoading.value = false
      }
    }
  }

  async function assignPolicy(policyId) {
    if (assignLoading.value) return
    assignLoading.value = true
    try {
      const current = await policiesApi.getAssignments(policyId)
      const groupIds = current.groups.map(g => g.group_id)
      if (!groupIds.includes(id)) groupIds.push(id)
      await policiesApi.assign(policyId, {
        is_global: current.is_global,
        group_ids: groupIds,
        agent_ids: current.agents.map(a => a.agent_id),
      })
      const policy = allPolicies.value.find(p => p.id === policyId)
      if (policy) policies.value.push(policy)
      assignOpen.value = false
      toast.success('Политика назначена')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка назначения')
    } finally {
      assignLoading.value = false
    }
  }

  async function unassignPolicy(policyId) {
    togglingPolicyId.value = policyId
    try {
      const current = await policiesApi.getAssignments(policyId)
      const groupIds = current.groups.map(g => g.group_id).filter(gid => gid !== id)
      await policiesApi.assign(policyId, {
        is_global: current.is_global,
        group_ids: groupIds,
        agent_ids: current.agents.map(a => a.agent_id),
      })
      policies.value = policies.value.filter(p => p.id !== policyId)
      toast.success('Политика снята')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка снятия политики')
    } finally {
      togglingPolicyId.value = null
    }
  }

  async function fetchGroup() {
    if (group.value) {
      localGroup.value = group.value
    } else {
      isLoading.value = true
      try {
        localGroup.value = await groupsApi.get(id)
      } catch {
        router.push('/groups')
      } finally {
        isLoading.value = false
      }
    }
  }

  async function fetchMembers() {
    membersLoading.value = true
    try {
      const data = await groupsApi.listAgents(id)
      members.value = data.items ?? data
    } catch {
      members.value = []
    } finally {
      membersLoading.value = false
    }
  }

  onMounted(async () => {
    await fetchGroup()
    await Promise.all([fetchMembers(), fetchPolicies()])
    if (!agentsStore.items.length) agentsStore.fetch()
  })

  // ── add member ─────────────────────────────────────────────
  const addOpen   = ref(false)
  const addSearch = ref('')
  const addLoading = ref(false)

  const memberIds = computed(() => new Set(members.value.map(a => a.id)))

  const availableAgents = computed(() => {
    const q = addSearch.value.trim().toLowerCase()
    return agentsStore.items.filter(a =>
      !memberIds.value.has(a.id) &&
      (!q || a.hostname.toLowerCase().includes(q) || (a.ip_address ?? '').includes(q))
    )
  })

  async function addMember(agentId) {
    addLoading.value = true
    try {
      await groupsApi.addAgents(id, [agentId])
      const agent = agentsStore.items.find(a => a.id === agentId)
      if (agent) members.value.push(agent)
      groupsStore.patchCount(id, +1)
      if (localGroup.value) {
        localGroup.value = { ...localGroup.value, agents_count: (localGroup.value.agents_count ?? 0) + 1 }
      }
      addOpen.value   = false
      addSearch.value = ''
      toast.success('Агент добавлен в группу')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка')
    } finally {
      addLoading.value = false
    }
  }

  // ── remove member ──────────────────────────────────────────
  const removeLoading = ref({})

  async function removeMember(agentId) {
    removeLoading.value = { ...removeLoading.value, [agentId]: true }
    try {
      await groupsApi.removeAgent(id, agentId)
      members.value = members.value.filter(a => a.id !== agentId)
      groupsStore.patchCount(id, -1)
      if (localGroup.value) {
        localGroup.value = { ...localGroup.value, agents_count: Math.max(0, (localGroup.value.agents_count ?? 0) - 1) }
      }
      toast.success('Агент удалён из группы')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка')
    } finally {
      const next = { ...removeLoading.value }
      delete next[agentId]
      removeLoading.value = next
    }
  }

  // ── edit group ─────────────────────────────────────────────
  const editOpen    = ref(false)
  const editForm    = ref({ name: '', description: '', color: '' })
  const editLoading = ref(false)
  const editError   = ref('')

  function openEdit() {
    if (!displayGroup.value) return
    editForm.value  = {
      name:        displayGroup.value.name,
      description: displayGroup.value.description ?? '',
      color:       displayGroup.value.color ?? '',
    }
    editError.value = ''
    editOpen.value  = true
  }

  async function submitEdit() {
    editLoading.value = true
    editError.value   = ''
    try {
      const updated = await groupsStore.update(id, {
        name:        editForm.value.name,
        description: editForm.value.description || null,
        color:       editForm.value.color || null,
      })
      localGroup.value = updated
      editOpen.value   = false
      toast.success('Группа обновлена')
    } catch (err) {
      editError.value = err.message ?? 'Ошибка сохранения'
    } finally {
      editLoading.value = false
    }
  }

  // ── delete group ───────────────────────────────────────────
  const deleteOpen    = ref(false)
  const deleteLoading = ref(false)

  async function confirmDelete() {
    deleteLoading.value = true
    try {
      await groupsStore.remove(id)
      toast.success('Группа удалена')
      router.push('/groups')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка удаления')
      deleteOpen.value = false
    } finally {
      deleteLoading.value = false
    }
  }

  return {
    displayGroup, isLoading,
    members, membersLoading,
    policies, policiesLoading,
    agentsStore,
    addOpen, addSearch, addLoading, availableAgents, addMember,
    removeLoading, removeMember,
    assignOpen, assignSearch, assignLoading, availablePolicies, allPoliciesLoading,
    togglingPolicyId, openAssign, assignPolicy, unassignPolicy,
    editOpen, editForm, editLoading, editError, openEdit, submitEdit,
    deleteOpen, deleteLoading, confirmDelete,
    colorDotStyle, fallbackColor,
    STATUS_DOT, formatLastSeen,
  }
}
