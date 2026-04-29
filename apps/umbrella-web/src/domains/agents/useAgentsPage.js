import { useAgentsStore }        from '@/domains/agents/store'
import { useGroupsStore }        from '@/domains/groups/store'
import { enrollmentTokensApi }   from '@/domains/agents/api'
import { useToast }              from '@/shared/composables/useToast'
import { usePagination }         from '@/shared/composables/usePagination'
import { usePolling }            from '@/shared/composables/usePolling'
import { lastAgentUpdate, agentsNeedRefresh } from '@/domains/agents/agentStreamEvents'
import {
  STATUS_LABELS, STATUS_CLASSES, STATUS_DOT,
  OS_LABELS, AGENT_STATUSES, AGENT_OS_LIST,
  formatLastSeen, formatDate,
} from '@/domains/agents/agents.utils'

export function useAgentsPage() {
  const store       = useAgentsStore()
  const groupsStore = useGroupsStore()
  const toast       = useToast()

  usePolling(() => store.fetch(), 30_000)

  // SSE: instant update when agent sends heartbeat
  watch(lastAgentUpdate, data => {
    if (!data) return
    const idx = store.items.findIndex(a => a.id === data.id)
    if (idx !== -1) store.items[idx] = data
  })

  // SSE: re-fetch all when stale-agent loop marks some offline
  watch(agentsNeedRefresh, async needsRefresh => {
    if (!needsRefresh) return
    agentsNeedRefresh.value = false
    await store.fetch()
  })

  // ── локальная фильтрация ──────────────────────────────────
  const searchQuery  = ref('')
  const activeStatus = ref(null)

  const filteredAgents = computed(() => {
    let list = store.items
    if (activeStatus.value) {
      list = list.filter(a => a.status === activeStatus.value)
    }
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase()
      list = list.filter(a =>
        a.hostname?.toLowerCase().includes(q) ||
        (a.ip_address ?? '').includes(q)
      )
    }
    return list
  })

  function setStatus(status) {
    activeStatus.value = activeStatus.value === status ? null : status
  }

  function resetFilters() {
    searchQuery.value  = ''
    activeStatus.value = null
  }

  const hasFilters = computed(() => searchQuery.value.trim() || activeStatus.value)

  const { page, totalPages, paged: pagedAgents, goTo } = usePagination(filteredAgents, 24)

  // ── edit ─────────────────────────────────────────────────
  const editOpen    = ref(false)
  const editTarget  = ref(null)
  const editForm    = ref({ notes: '' })
  const editLoading = ref(false)
  const editError   = ref('')

  function openEdit(agent) {
    editTarget.value = agent
    editForm.value   = { notes: agent.notes ?? '' }
    editError.value  = ''
    editOpen.value   = true
  }

  async function submitEdit() {
    if (!editTarget.value) return
    editLoading.value = true
    editError.value   = ''
    try {
      await store.update(editTarget.value.id, {
        notes: editForm.value.notes || null,
      })
      editOpen.value = false
      toast.success('Агент обновлён')
    } catch (err) {
      editError.value = err.message ?? 'Ошибка сохранения'
    } finally {
      editLoading.value = false
    }
  }

  // ── enrollment tokens ─────────────────────────────────────
  const enrollOpen    = ref(false)
  const enrollForm    = ref({ note: '', expires_in_days: 1, group_id: null, max_uses: null })
  const enrollLoading = ref(false)
  const enrollError   = ref('')
  const enrollCreated = ref(null)
  const enrollCopied  = ref(false)
  const enrollCmdCopied = ref(false)

  const tokenList        = ref([])
  const tokenListLoading = ref(false)

  async function fetchTokenList() {
    tokenListLoading.value = true
    try {
      tokenList.value = await enrollmentTokensApi.list()
    } catch {
      tokenList.value = []
    } finally {
      tokenListLoading.value = false
    }
  }

  function openEnroll() {
    enrollForm.value      = { note: '', expires_in_days: 1, group_id: null, max_uses: null }
    enrollError.value     = ''
    enrollCreated.value   = null
    enrollCopied.value    = false
    enrollCmdCopied.value = false
    enrollOpen.value      = true
    fetchTokenList()
    if (!groupsStore.items.length) groupsStore.fetch()
  }

  function handleEnrollClose(v) {
    enrollOpen.value = v
    if (!v) { enrollCreated.value = null; enrollCmdCopied.value = false }
  }

  function copyEnrollCmd() {
    const url = import.meta.env.VITE_API_BASE_URL ?? window.location.origin
    const cmd = `umbrella-agent --token ${enrollCreated.value.raw_token} --server ${url}`
    navigator.clipboard.writeText(cmd)
    enrollCmdCopied.value = true
    setTimeout(() => { enrollCmdCopied.value = false }, 2000)
  }

  async function submitEnroll() {
    enrollLoading.value = true
    enrollError.value   = ''
    try {
      const result = await enrollmentTokensApi.create({
        note:            enrollForm.value.note || null,
        expires_in_days: enrollForm.value.expires_in_days,
        group_id:        enrollForm.value.group_id || null,
        max_uses:        enrollForm.value.max_uses || null,
      })
      enrollCreated.value = result
      fetchTokenList()
    } catch (err) {
      enrollError.value = err.message ?? 'Ошибка создания токена'
    } finally {
      enrollLoading.value = false
    }
  }

  function copyEnrollToken() {
    navigator.clipboard.writeText(enrollCreated.value.raw_token)
    enrollCopied.value = true
    setTimeout(() => { enrollCopied.value = false }, 2000)
  }

  async function revokeEnrollToken(id) {
    try {
      await enrollmentTokensApi.revoke(id)
      tokenList.value = tokenList.value.filter(t => t.id !== id)
      toast.success('Токен отозван')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка отзыва токена')
    }
  }

  // ── delete ───────────────────────────────────────────────
  const deleteTarget  = ref(null)
  const deleteLoading = ref(false)

  function openDelete(agent)  { deleteTarget.value = agent }
  function closeDelete()      { deleteTarget.value = null  }

  async function confirmDelete() {
    if (!deleteTarget.value) return
    deleteLoading.value = true
    try {
      await store.remove(deleteTarget.value.id)
      toast.success('Агент удалён')
      deleteTarget.value = null
    } catch (err) {
      toast.error(err.message ?? 'Ошибка удаления')
      deleteTarget.value = null
    } finally {
      deleteLoading.value = false
    }
  }

  return {
    store,
    filteredAgents, pagedAgents, page, totalPages, goTo,
    searchQuery, activeStatus, hasFilters,
    STATUS_LABELS, STATUS_CLASSES, STATUS_DOT,
    OS_LABELS, AGENT_STATUSES, AGENT_OS_LIST,
    formatLastSeen, formatDate,
    setStatus, resetFilters,
    editOpen, editForm, editLoading, editError, openEdit, submitEdit,
    enrollOpen, enrollForm, enrollLoading, enrollError, enrollCreated, enrollCopied, enrollCmdCopied,
    tokenList, tokenListLoading,
    groupsStore,
    openEnroll, handleEnrollClose, submitEnroll, copyEnrollToken, copyEnrollCmd, revokeEnrollToken,
    deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
  }
}
