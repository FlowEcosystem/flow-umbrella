import { useAgentsStore } from '@/domains/agents/store'
import { useGroupsStore } from '@/domains/groups/store'
import { groupsApi } from '@/domains/groups/api'
import { useToast } from '@/shared/composables/useToast'

export function useBulkAgents() {
  const agentsStore = useAgentsStore()
  const groupsStore = useGroupsStore()
  const toast = useToast()

  const selectedIds = ref(new Set())
  const bulkStatusLoading = ref(false)
  const bulkGroupLoading = ref(false)

  const selectedCount = computed(() => selectedIds.value.size)
  const hasSelection = computed(() => selectedIds.value.size > 0)

  function toggle(id) {
    const next = new Set(selectedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    selectedIds.value = next
  }

  function isSelected(id) {
    return selectedIds.value.has(id)
  }

  function selectAll(ids) {
    selectedIds.value = new Set(ids)
  }

  function clearSelection() {
    selectedIds.value = new Set()
  }

  async function bulkSetStatus(status) {
    if (!selectedIds.value.size) return
    bulkStatusLoading.value = true
    const ids = [...selectedIds.value]
    try {
      await Promise.all(ids.map(id => agentsStore.update(id, { status })))
      toast.success(`Статус обновлён у ${ids.length} агент${_suffix(ids.length)}`)
      clearSelection()
    } catch {
      toast.error('Не удалось обновить статус')
    } finally {
      bulkStatusLoading.value = false
    }
  }

  async function bulkAddToGroup(groupId) {
    if (!selectedIds.value.size) return
    bulkGroupLoading.value = true
    const ids = [...selectedIds.value]
    try {
      await groupsApi.addAgents(groupId, ids)
      const group = groupsStore.items.find(g => g.id === groupId)
      toast.success(`${ids.length} агент${_suffix(ids.length)} добавлен${ids.length === 1 ? '' : 'о'} в группу${group ? ` «${group.name}»` : ''}`)
      clearSelection()
    } catch {
      toast.error('Не удалось добавить в группу')
    } finally {
      bulkGroupLoading.value = false
    }
  }

  function _suffix(n) {
    const mod10 = n % 10
    const mod100 = n % 100
    if (mod100 >= 11 && mod100 <= 19) return 'ов'
    if (mod10 === 1) return ''
    if (mod10 >= 2 && mod10 <= 4) return 'а'
    return 'ов'
  }

  return {
    selectedIds,
    selectedCount,
    hasSelection,
    bulkStatusLoading,
    bulkGroupLoading,
    toggle,
    isSelected,
    selectAll,
    clearSelection,
    bulkSetStatus,
    bulkAddToGroup,
  }
}
