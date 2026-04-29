import { getAccessToken } from '@/app/api/http'
import { useAlerts }      from '@/shared/composables/useAlerts'
import { useToast }       from '@/shared/composables/useToast'
import { lastAgentUpdate, agentsNeedRefresh } from '@/domains/agents/agentStreamEvents'

export function useGlobalStream() {
  const { addAlert } = useAlerts()
  const toast = useToast()
  let es = null

  function connect() {
    const token = getAccessToken()
    if (!token) return
    const url = `/v1/stream?token=${encodeURIComponent(token)}`
    es = new EventSource(url)
    es.addEventListener('alert', e => {
      const data = JSON.parse(e.data)
      addAlert(data)
      const host = data.hostname ?? data.agent_id?.slice(0, 8)
      toast.error(`Опасный процесс: ${data.process_name} (${host})`)
    })
    es.addEventListener('agent_update', e => {
      lastAgentUpdate.value = JSON.parse(e.data)
    })
    es.addEventListener('agents_refresh', () => {
      agentsNeedRefresh.value = true
    })
    es.addEventListener('ping', () => {})
    es.onerror = () => {
      es.close()
      es = null
      setTimeout(connect, 5_000)
    }
  }

  onMounted(connect)
  onUnmounted(() => { es?.close(); es = null })
}
