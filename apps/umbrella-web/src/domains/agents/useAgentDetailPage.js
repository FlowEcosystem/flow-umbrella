import { useAgentsStore }  from '@/domains/agents/store'
import { useGroupsStore }  from '@/domains/groups/store'
import { useToast }        from '@/shared/composables/useToast'
import { usePolling }      from '@/shared/composables/usePolling'
import { agentsApi }       from '@/domains/agents/api'
import { groupsApi }       from '@/domains/groups/api'
import {
  STATUS_LABELS, STATUS_CLASSES, STATUS_DOT, OS_LABELS, formatLastSeen, formatDate,
} from '@/domains/agents/agents.utils'
import { colorDotStyle, fallbackColor } from '@/domains/groups/groups.utils'

export function useAgentDetailPage(id) {
  const agentsStore = useAgentsStore()
  const groupsStore = useGroupsStore()
  const toast       = useToast()
  const router      = useRouter()

  const agent = computed(() => agentsStore.items.find(a => a.id === id))

  const isLoading  = ref(false)
  const localAgent = ref(null)

  const displayAgent = computed(() => localAgent.value ?? agent.value ?? null)

  // ── agent groups ───────────────────────────────────────────
  const groups        = ref([])
  const groupsLoading = ref(false)

  // ── agent policies ─────────────────────────────────────────
  const policies        = ref([])
  const policiesLoading = ref(false)

  async function fetchPolicies() {
    policiesLoading.value = true
    try {
      policies.value = await agentsApi.listPolicies(id)
    } catch {
      policies.value = []
    } finally {
      policiesLoading.value = false
    }
  }

  async function fetchAgent() {
    if (agent.value) {
      localAgent.value = agent.value
    } else {
      isLoading.value = true
      try {
        localAgent.value = await agentsApi.get(id)
      } catch {
        router.push('/agents')
      } finally {
        isLoading.value = false
      }
    }
  }

  async function fetchGroups() {
    groupsLoading.value = true
    try {
      const data = await agentsApi.listGroups(id)
      groups.value = data.items ?? data
    } catch {
      groups.value = []
    } finally {
      groupsLoading.value = false
    }
  }

  async function pollAgent() {
    try {
      const data = await agentsApi.get(id)
      localAgent.value = data
      const idx = agentsStore.items.findIndex(a => a.id === id)
      if (idx !== -1) agentsStore.items[idx] = data
    } catch { /* silent */ }
  }

  // ── metrics ────────────────────────────────────────────────
  const metricsHistory  = ref([])
  const metricsLoading  = ref(false)

  const latestMetric = computed(() => metricsHistory.value[0] ?? null)

  function metricPct(used, total) {
    if (!total) return 0
    return Math.round((used / total) * 100)
  }

  async function fetchMetrics() {
    metricsLoading.value = true
    try {
      metricsHistory.value = await agentsApi.getMetrics(id, 60)
    } catch {
      metricsHistory.value = []
    } finally {
      metricsLoading.value = false
    }
  }

  onMounted(async () => {
    await fetchAgent()
    await Promise.all([fetchGroups(), fetchPolicies(), fetchCommands(), fetchMetrics()])
    if (!groupsStore.items.length) groupsStore.fetch()
  })

  usePolling(pollAgent, 30_000, { immediate: false })

  // ── commands ───────────────────────────────────────────────
  const commands        = ref([])
  const commandsLoading = ref(false)

  const COMMAND_TYPES = ['reboot', 'collect_diagnostics', 'update_self', 'apply_config', 'sync_policies']
  const COMMAND_TYPE_LABELS = {
    reboot:               'Перезагрузка',
    collect_diagnostics:  'Сбор диагностики',
    update_self:          'Обновить агент',
    apply_config:         'Применить конфиг',
    sync_policies:        'Синхр. политики',
    decommission:         'Деинсталляция',
  }
  const COMMAND_STATUS_LABELS = {
    pending:      'Ожидает',
    sent:         'Отправлена',
    acknowledged: 'Принята',
    success:      'Выполнена',
    failure:      'Ошибка',
    timeout:      'Таймаут',
  }

  async function fetchCommands() {
    commandsLoading.value = true
    try {
      commands.value = await agentsApi.listCommands(id)
    } catch {
      commands.value = []
    } finally {
      commandsLoading.value = false
    }
  }

  const cmdOpen    = ref(false)
  const cmdType    = ref('reboot')
  const cmdPayload = ref('')
  const cmdLoading = ref(false)
  const cmdError   = ref('')

  function openCmdDialog() {
    cmdType.value    = 'reboot'
    cmdPayload.value = ''
    cmdError.value   = ''
    cmdOpen.value    = true
  }

  async function submitCommand() {
    cmdError.value = ''
    let parsedPayload = null
    if (cmdPayload.value.trim()) {
      try {
        parsedPayload = JSON.parse(cmdPayload.value.trim())
      } catch {
        cmdError.value = 'Некорректный JSON в payload'
        return
      }
    }
    cmdLoading.value = true
    try {
      const cmd = await agentsApi.issueCommand(id, { type: cmdType.value, payload: parsedPayload })
      commands.value = [cmd, ...commands.value]
      cmdOpen.value  = false
      toast.success('Команда отправлена')
    } catch (err) {
      cmdError.value = err.message ?? 'Ошибка отправки команды'
    } finally {
      cmdLoading.value = false
    }
  }

  // ── offline decommission token ─────────────────────────────
  const offlineTokenOpen    = ref(false)
  const offlineTokenData    = ref(null)
  const offlineTokenLoading = ref(false)
  const offlineTokenCopied  = ref(false)

  async function generateOfflineToken() {
    offlineTokenLoading.value = true
    try {
      const data = await agentsApi.generateDecommissionToken(id)
      offlineTokenData.value   = data
      offlineTokenCopied.value = false
      offlineTokenOpen.value   = true
    } catch (err) {
      toast.error(err.message ?? 'Ошибка генерации токена')
    } finally {
      offlineTokenLoading.value = false
    }
  }

  function copyOfflineToken() {
    navigator.clipboard.writeText(offlineTokenData.value.token)
    offlineTokenCopied.value = true
    setTimeout(() => { offlineTokenCopied.value = false }, 2000)
  }

  // ── decommission ───────────────────────────────────────────
  const decommissionOpen    = ref(false)
  const decommissionLoading = ref(false)

  async function confirmDecommission() {
    decommissionLoading.value = true
    try {
      await agentsApi.issueCommand(id, { type: 'decommission' })
      await agentsStore.update(id, { status: 'decommissioned' })
      localAgent.value = { ...localAgent.value, status: 'decommissioned' }
      decommissionOpen.value = false
      toast.success('Команда деинсталляции отправлена')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка')
      decommissionOpen.value = false
    } finally {
      decommissionLoading.value = false
    }
  }

  // ── add to group ───────────────────────────────────────────
  const addGroupOpen   = ref(false)
  const addGroupSearch = ref('')
  const addLoading     = ref(false)

  const groupIds = computed(() => new Set(groups.value.map(g => g.id)))

  const availableGroups = computed(() => {
    const q = addGroupSearch.value.trim().toLowerCase()
    return groupsStore.items.filter(g =>
      !groupIds.value.has(g.id) &&
      (!q || g.name.toLowerCase().includes(q))
    )
  })

  async function addToGroup(groupId) {
    addLoading.value = true
    try {
      await groupsApi.addAgents(groupId, [id])
      const group = groupsStore.items.find(g => g.id === groupId)
      if (group) groups.value.push(group)
      groupsStore.patchCount(groupId, +1)
      addGroupOpen.value   = false
      addGroupSearch.value = ''
      toast.success('Агент добавлен в группу')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка')
    } finally {
      addLoading.value = false
    }
  }

  // ── remove from group ──────────────────────────────────────
  const removeLoading = ref({})

  async function removeFromGroup(groupId) {
    removeLoading.value = { ...removeLoading.value, [groupId]: true }
    try {
      await groupsApi.removeAgent(groupId, id)
      groups.value = groups.value.filter(g => g.id !== groupId)
      groupsStore.patchCount(groupId, -1)
      toast.success('Агент удалён из группы')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка')
    } finally {
      const next = { ...removeLoading.value }
      delete next[groupId]
      removeLoading.value = next
    }
  }

  // ── edit agent ─────────────────────────────────────────────
  const editOpen    = ref(false)
  const editForm    = ref({ hostname: '', status: '', notes: '' })
  const editLoading = ref(false)
  const editError   = ref('')

  function openEdit() {
    if (!displayAgent.value) return
    editForm.value  = {
      hostname: displayAgent.value.hostname,
      status:   displayAgent.value.status,
      notes:    displayAgent.value.notes ?? '',
    }
    editError.value = ''
    editOpen.value  = true
  }

  async function submitEdit() {
    editLoading.value = true
    editError.value   = ''
    try {
      const updated = await agentsStore.update(id, {
        hostname: editForm.value.hostname,
        status:   editForm.value.status,
        notes:    editForm.value.notes || null,
      })
      localAgent.value = updated
      editOpen.value   = false
      toast.success('Агент обновлён')
    } catch (err) {
      editError.value = err.message ?? 'Ошибка сохранения'
    } finally {
      editLoading.value = false
    }
  }

  // ── regen token ────────────────────────────────────────────
  const regenOpen    = ref(false)
  const regenLoading = ref(false)
  const tokenData    = ref(null)
  const tokenOpen    = ref(false)
  const tokenCopied  = ref(false)

  async function confirmRegen() {
    regenLoading.value = true
    try {
      const result = await agentsStore.regenerateToken(id)
      regenOpen.value   = false
      tokenData.value   = result
      tokenCopied.value = false
      tokenOpen.value   = true
    } catch (err) {
      toast.error(err.message ?? 'Ошибка перевыпуска токена')
    } finally {
      regenLoading.value = false
    }
  }

  function copyToken() {
    navigator.clipboard.writeText(tokenData.value.enrollment_token)
    tokenCopied.value = true
    setTimeout(() => { tokenCopied.value = false }, 2000)
  }

  // ── delete agent ───────────────────────────────────────────
  const deleteOpen    = ref(false)
  const deleteLoading = ref(false)

  async function confirmDelete() {
    deleteLoading.value = true
    try {
      await agentsStore.remove(id)
      toast.success('Агент удалён')
      router.push('/agents')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка удаления')
      deleteOpen.value = false
    } finally {
      deleteLoading.value = false
    }
  }

  return {
    displayAgent, isLoading,
    offlineTokenOpen, offlineTokenData, offlineTokenLoading, offlineTokenCopied,
    generateOfflineToken, copyOfflineToken,
    decommissionOpen, decommissionLoading, confirmDecommission,
    groups, groupsLoading,
    policies, policiesLoading,
    commands, commandsLoading,
    groupsStore,
    addGroupOpen, addGroupSearch, addLoading, availableGroups, addToGroup,
    removeLoading, removeFromGroup,
    STATUS_LABELS, STATUS_CLASSES, STATUS_DOT, OS_LABELS,
    formatLastSeen, formatDate,
    colorDotStyle, fallbackColor,
    editOpen, editForm, editLoading, editError, openEdit, submitEdit,
    regenOpen, regenLoading, confirmRegen,
    tokenData, tokenOpen, tokenCopied, copyToken,
    deleteOpen, deleteLoading, confirmDelete,
    COMMAND_TYPES, COMMAND_TYPE_LABELS, COMMAND_STATUS_LABELS,
    cmdOpen, cmdType, cmdPayload, cmdLoading, cmdError, openCmdDialog, submitCommand, fetchCommands,
    metricsHistory, metricsLoading, latestMetric, metricPct,
  }
}
