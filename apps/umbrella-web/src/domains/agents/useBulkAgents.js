import { useGroupsStore } from '@/domains/groups/store'
import { groupsApi }     from '@/domains/groups/api'
import { agentsApi }     from '@/domains/agents/api'
import { useToast }      from '@/shared/composables/useToast'

export function useBulkAgents() {
  const groupsStore = useGroupsStore()
  const toast       = useToast()

  const selectedIds = ref(new Set())

  const selectedCount = computed(() => selectedIds.value.size)
  const hasSelection  = computed(() => selectedIds.value.size > 0)

  function toggle(id) {
    const next = new Set(selectedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    selectedIds.value = next
  }

  function isSelected(id) { return selectedIds.value.has(id) }
  function selectAll(ids)  { selectedIds.value = new Set(ids) }
  function clearSelection(){ selectedIds.value = new Set() }

  // ── bulk add to group ─────────────────────────────────────
  const bulkGroupLoading = ref(false)

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

  // ── bulk decommission ─────────────────────────────────────
  const bulkDecommissionOpen    = ref(false)
  const bulkDecommissionLoading = ref(false)

  function openBulkDecommission() {
    if (!selectedIds.value.size) return
    bulkDecommissionOpen.value = true
  }

  async function confirmBulkDecommission() {
    bulkDecommissionLoading.value = true
    const ids = [...selectedIds.value]
    const results = await Promise.allSettled(
      ids.map(id => agentsApi.issueCommand(id, { type: 'decommission' }))
    )
    const ok      = results.filter(r => r.status === 'fulfilled').length
    const failed  = results.length - ok
    if (ok)     toast.success(`Команда деинсталляции отправлена ${ok} агент${_suffix(ok)}`)
    if (failed) toast.error(`Не удалось отправить ${failed} команд${_suffix(failed)}`)
    bulkDecommissionOpen.value    = false
    bulkDecommissionLoading.value = false
    clearSelection()
  }

  function _suffix(n) {
    const mod10 = n % 10
    const mod100 = n % 100
    if (mod100 >= 11 && mod100 <= 19) return 'ам'
    if (mod10 === 1) return 'у'
    if (mod10 >= 2 && mod10 <= 4) return 'ам'
    return 'ам'
  }

  return {
    selectedIds, selectedCount, hasSelection,
    toggle, isSelected, selectAll, clearSelection,
    bulkGroupLoading, bulkAddToGroup,
    bulkDecommissionOpen, bulkDecommissionLoading,
    openBulkDecommission, confirmBulkDecommission,
  }
}
