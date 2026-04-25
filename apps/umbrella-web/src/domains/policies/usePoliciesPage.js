import { usePoliciesStore } from '@/domains/policies/store'
import { usePagination }   from '@/shared/composables/usePagination'
import { useToast }        from '@/shared/composables/useToast'

export const POLICY_ACTIONS   = ['block', 'allow']
export const POLICY_SOURCES   = ['local', 'global']
export const RULE_TYPES         = ['domain', 'url', 'ip']
export const PROCESS_RULE_TYPES = ['process']

export const ACTION_LABELS  = { block: 'Блокировать', allow: 'Разрешить' }
export const SOURCE_LABELS  = { local: 'Локальная',   global: 'Глобальная' }
export const RULE_LABELS    = { domain: 'Домен', url: 'URL', ip: 'IP / CIDR', process: 'Процесс' }

export const SORT_COLS = [
  { key: 'name',        label: 'Название' },
  { key: 'rules_count', label: 'Правила'  },
  { key: 'is_active',   label: 'Статус'   },
]

export function usePoliciesPage() {
  const store = usePoliciesStore()
  const toast = useToast()

  onMounted(() => store.fetch())

  // --- filters ---
  const searchQuery  = ref('')
  const activeAction = ref(null)
  const activeSource = ref(null)

  const hasFilters = computed(() =>
    !!searchQuery.value || activeAction.value !== null || activeSource.value !== null
  )

  function setAction(v) { activeAction.value = activeAction.value === v ? null : v }
  function setSource(v) { activeSource.value = activeSource.value === v ? null : v }
  function resetFilters() { searchQuery.value = ''; activeAction.value = null; activeSource.value = null }

  const filteredPolicies = computed(() => {
    let list = store.items.filter(p => (p.kind ?? 'traffic') !== 'process')
    const q = searchQuery.value.trim().toLowerCase()
    if (q) list = list.filter(p => p.name.toLowerCase().includes(q) || (p.description ?? '').toLowerCase().includes(q))
    if (activeAction.value) list = list.filter(p => p.action === activeAction.value)
    if (activeSource.value) list = list.filter(p => p.source === activeSource.value)
    return list
  })

  // --- sorting ---
  const sortBy  = ref(null)
  const sortDir = ref('asc')

  function setSort(col) {
    if (sortBy.value === col) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy.value = col
      sortDir.value = 'asc'
    }
  }

  const sortedPolicies = computed(() => {
    if (!sortBy.value) return filteredPolicies.value
    const col = sortBy.value
    return [...filteredPolicies.value].sort((a, b) => {
      let va = col === 'rules_count' ? (a.rules_count ?? 0) : a[col]
      let vb = col === 'rules_count' ? (b.rules_count ?? 0) : b[col]
      if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase() }
      if (va === vb) return 0
      const cmp = va > vb ? 1 : -1
      return sortDir.value === 'asc' ? cmp : -cmp
    })
  })

  const { page, totalPages, paged: pagedPolicies, goTo } = usePagination(sortedPolicies, 24)

  // --- bulk selection ---
  const selectedIds = ref([])

  const hasSelection   = computed(() => selectedIds.value.length > 0)
  const selectionCount = computed(() => selectedIds.value.length)

  const allOnPageSelected = computed(() => {
    const local = pagedPolicies.value.filter(p => p.source === 'local')
    return local.length > 0 && local.every(p => selectedIds.value.includes(p.id))
  })

  function isSelected(id) { return selectedIds.value.includes(id) }

  function toggleSelect(id) {
    selectedIds.value = isSelected(id)
      ? selectedIds.value.filter(x => x !== id)
      : [...selectedIds.value, id]
  }

  function toggleSelectAll() {
    const localIds = pagedPolicies.value.filter(p => p.source === 'local').map(p => p.id)
    if (allOnPageSelected.value) {
      selectedIds.value = selectedIds.value.filter(id => !localIds.includes(id))
    } else {
      selectedIds.value = [...new Set([...selectedIds.value, ...localIds])]
    }
  }

  function clearSelection() { selectedIds.value = [] }

  // remove deselected items from selection when filter changes
  watch(filteredPolicies, (newList) => {
    const validIds = new Set(newList.map(p => p.id))
    selectedIds.value = selectedIds.value.filter(id => validIds.has(id))
  })

  // --- bulk operations ---
  const bulkLoading    = ref(false)
  const bulkDeleteOpen = ref(false)

  async function bulkToggleActive(active) {
    const ids = [...selectedIds.value]
    ids.forEach(id => {
      const idx = store.items.findIndex(p => p.id === id)
      if (idx !== -1) store.items[idx].is_active = active
    })
    bulkLoading.value = true
    try {
      await Promise.all(ids.map(id => store.update(id, { is_active: active })))
      toast.success(`${ids.length} ${_policyWord(ids.length)} обновлено`)
      clearSelection()
    } catch {
      ids.forEach(id => {
        const idx = store.items.findIndex(p => p.id === id)
        if (idx !== -1) store.items[idx].is_active = !active
      })
      toast.error('Не удалось обновить статус')
    } finally {
      bulkLoading.value = false
    }
  }

  async function bulkDuplicate() {
    const policies = selectedIds.value
      .map(id => store.items.find(p => p.id === id))
      .filter(Boolean)
    bulkLoading.value = true
    try {
      await Promise.all(policies.map(p => store.create({
        name:         `${p.name} (копия)`,
        description:  p.description,
        kind:         p.kind,
        action:       p.action,
        is_active:    false,
        service_ids:  p.services.map(s => s.id),
        custom_rules: p.custom_rules.map(r => ({ ...r })),
      })))
      toast.success(`${policies.length} ${_policyWord(policies.length)} продублировано`)
      clearSelection()
    } catch {
      toast.error('Не удалось продублировать')
    } finally {
      bulkLoading.value = false
    }
  }

  async function bulkDelete() {
    const ids = [...selectedIds.value]
    bulkDeleteOpen.value = false
    bulkLoading.value = true
    try {
      await Promise.all(ids.map(id => store.remove(id)))
      toast.success(`${ids.length} ${_policyWord(ids.length)} удалено`)
      clearSelection()
    } catch {
      toast.error('Не удалось удалить некоторые политики')
      await store.fetch()
    } finally {
      bulkLoading.value = false
    }
  }

  function _policyWord(n) {
    const m10 = n % 10, m100 = n % 100
    if (m100 >= 11 && m100 <= 19) return 'политик'
    if (m10 === 1) return 'политика'
    if (m10 >= 2 && m10 <= 4) return 'политики'
    return 'политик'
  }

  // --- create / edit form ---
  const formOpen    = ref(false)
  const formTarget  = ref(null)
  const formLoading = ref(false)
  const formError   = ref('')
  const flashId     = ref(null)

  const emptyForm = () => ({
    name: '', description: '', action: 'block', is_active: true,
    service_ids: [], custom_rules: [],
  })
  const formData = ref(emptyForm())

  function openCreate() {
    formTarget.value = null
    formData.value = emptyForm()
    formError.value = ''
    formOpen.value = true
  }

  function openEdit(policy) {
    formTarget.value = policy
    formData.value = {
      name:         policy.name,
      description:  policy.description ?? '',
      action:       policy.action,
      is_active:    policy.is_active,
      service_ids:  policy.services.map(s => s.id),
      custom_rules: policy.custom_rules.map(r => ({ ...r })),
    }
    formError.value = ''
    formOpen.value = true
  }

  async function submitForm() {
    formLoading.value = true
    formError.value = ''
    try {
      const payload = {
        name:         formData.value.name.trim(),
        description:  formData.value.description.trim() || null,
        action:       formData.value.action,
        is_active:    formData.value.is_active,
        service_ids:  formData.value.service_ids,
        custom_rules: formData.value.custom_rules,
      }
      let saved
      if (formTarget.value) {
        saved = await store.update(formTarget.value.id, payload)
        toast.success('Политика обновлена')
      } else {
        saved = await store.create(payload)
        toast.success('Политика создана')
      }
      flashId.value = saved.id
      setTimeout(() => { flashId.value = null }, 1800)
      formOpen.value = false
    } catch (err) {
      formError.value = err.response?.data?.message ?? 'Ошибка сохранения'
    } finally {
      formLoading.value = false
    }
  }

  // --- inline toggle active ---
  const toggleLoading = ref({})

  async function toggleActive(policy) {
    const idx  = store.items.findIndex(p => p.id === policy.id)
    const prev = policy.is_active
    if (idx !== -1) store.items[idx].is_active = !prev
    toggleLoading.value[policy.id] = true
    try {
      await store.update(policy.id, { is_active: !prev })
    } catch {
      if (idx !== -1) store.items[idx].is_active = prev
      toast.error('Не удалось изменить статус')
    } finally {
      delete toggleLoading.value[policy.id]
    }
  }

  // --- expandable row ---
  const expandedId = ref(null)

  function toggleExpand(id) {
    expandedId.value = expandedId.value === id ? null : id
  }

  // --- duplicate ---
  const duplicateLoading = ref({})

  async function duplicatePolicy(policy) {
    duplicateLoading.value[policy.id] = true
    try {
      const created = await store.create({
        name:         `${policy.name} (копия)`,
        description:  policy.description,
        kind:         policy.kind,
        action:       policy.action,
        is_active:    false,
        service_ids:  policy.services.map(s => s.id),
        custom_rules: policy.custom_rules.map(r => ({ ...r })),
      })
      flashId.value = created.id
      setTimeout(() => { flashId.value = null }, 1800)
      toast.success('Политика продублирована')
    } catch {
      toast.error('Не удалось продублировать политику')
    } finally {
      delete duplicateLoading.value[policy.id]
    }
  }

  // --- delete ---
  const deleteTarget  = ref(null)
  const deleteLoading = ref(false)

  function openDelete(policy)  { deleteTarget.value = policy }
  function closeDelete()       { deleteTarget.value = null }

  async function confirmDelete() {
    if (!deleteTarget.value) return
    deleteLoading.value = true
    try {
      await store.remove(deleteTarget.value.id)
      toast.success('Политика удалена')
      deleteTarget.value = null
    } catch {
      toast.error('Не удалось удалить политику')
    } finally {
      deleteLoading.value = false
    }
  }

  return {
    store,
    filteredPolicies, pagedPolicies, page, totalPages, goTo,
    searchQuery, activeAction, activeSource, hasFilters,
    setAction, setSource, resetFilters,
    sortBy, sortDir, setSort,
    selectedIds, hasSelection, selectionCount, allOnPageSelected,
    isSelected, toggleSelect, toggleSelectAll, clearSelection,
    bulkLoading, bulkDeleteOpen, bulkToggleActive, bulkDuplicate, bulkDelete,
    formOpen, formTarget, formData, formLoading, formError, flashId,
    openCreate, openEdit, submitForm,
    toggleLoading, toggleActive,
    expandedId, toggleExpand,
    duplicateLoading, duplicatePolicy,
    deleteTarget, deleteLoading, openDelete, closeDelete, confirmDelete,
    ACTION_LABELS, SOURCE_LABELS, RULE_LABELS, POLICY_ACTIONS, POLICY_SOURCES, RULE_TYPES,
  }
}
