import { useAgentsStore }  from '@/domains/agents/store'
import { useToast }        from '@/shared/composables/useToast'
import { usePagination }   from '@/shared/composables/usePagination'
import { usePolling }      from '@/shared/composables/usePolling'
import {
  STATUS_LABELS, STATUS_CLASSES, STATUS_DOT,
  OS_LABELS, AGENT_STATUSES, AGENT_OS_LIST,
  formatLastSeen, formatDate,
} from '@/domains/agents/agents.utils'

export function useAgentsPage() {
  const store = useAgentsStore()
  const toast = useToast()

  usePolling(() => store.fetch(), 30_000)

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
        a.hostname.toLowerCase().includes(q) ||
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

  // ── create ───────────────────────────────────────────────
  const createOpen    = ref(false)
  const createForm    = ref({ hostname: '', os: 'linux', notes: '' })
  const createLoading = ref(false)
  const createError   = ref('')

  function openCreate() {
    createForm.value  = { hostname: '', os: 'linux', notes: '' }
    createError.value = ''
    createOpen.value  = true
  }

  async function submitCreate() {
    createLoading.value = true
    createError.value   = ''
    try {
      const result = await store.create({
        hostname: createForm.value.hostname,
        os:       createForm.value.os,
        notes:    createForm.value.notes || null,
      })
      createOpen.value = false
      await store.fetch()
      openToken(result)
    } catch (err) {
      createError.value = err.message ?? 'Ошибка создания'
    } finally {
      createLoading.value = false
    }
  }

  // ── edit ─────────────────────────────────────────────────
  const editOpen    = ref(false)
  const editTarget  = ref(null)
  const editForm    = ref({ hostname: '', status: '', notes: '' })
  const editLoading = ref(false)
  const editError   = ref('')

  function openEdit(agent) {
    editTarget.value = agent
    editForm.value   = { hostname: agent.hostname, status: agent.status, notes: agent.notes ?? '' }
    editError.value  = ''
    editOpen.value   = true
  }

  async function submitEdit() {
    if (!editTarget.value) return
    editLoading.value = true
    editError.value   = ''
    try {
      await store.update(editTarget.value.id, {
        hostname: editForm.value.hostname,
        status:   editForm.value.status,
        notes:    editForm.value.notes || null,
      })
      editOpen.value = false
      toast.success('Агент обновлён')
    } catch (err) {
      editError.value = err.message ?? 'Ошибка сохранения'
    } finally {
      editLoading.value = false
    }
  }

  // ── token ────────────────────────────────────────────────
  const tokenOpen   = ref(false)
  const tokenData   = ref(null)
  const tokenCopied = ref(false)

  function openToken(data) {
    tokenData.value   = data
    tokenCopied.value = false
    tokenOpen.value   = true
  }

  function copyToken() {
    navigator.clipboard.writeText(tokenData.value.enrollment_token)
    tokenCopied.value = true
    setTimeout(() => { tokenCopied.value = false }, 2000)
  }

  // ── regen token confirm ───────────────────────────────────
  const regenTarget  = ref(null)
  const regenLoading = ref(false)

  function openRegenConfirm(agent) { regenTarget.value = agent }
  function closeRegenConfirm()     { regenTarget.value = null  }

  async function confirmRegen() {
    if (!regenTarget.value) return
    regenLoading.value = true
    try {
      const result = await store.regenerateToken(regenTarget.value.id)
      regenTarget.value = null
      openToken(result)
    } catch (err) {
      toast.error(err.message ?? 'Ошибка перевыпуска токена')
    } finally {
      regenLoading.value = false
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
    createOpen, createForm, createLoading, createError, openCreate, submitCreate,
    editOpen, editForm, editLoading, editError, openEdit, submitEdit,
    tokenOpen, tokenData, tokenCopied, openToken, copyToken,
    regenTarget, regenLoading, openRegenConfirm, closeRegenConfirm, confirmRegen,
    deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
  }
}
