// Module-level reactive state — shared across all components.
const alerts = ref([])  // { agent_id, hostname, process_name, detected_at }
const unread  = ref(0)

export function useAlerts() {
  function addAlert(data) {
    alerts.value = [data, ...alerts.value].slice(0, 100)
    unread.value++
  }

  function clearUnread() {
    unread.value = 0
  }

  return { alerts, unread, addAlert, clearUnread }
}
