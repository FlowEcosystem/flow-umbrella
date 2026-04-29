import { getAccessToken } from '@/app/api/http'

export function useAgentStream(agentId, { onAgent, onMetrics, onProcesses, onCommand } = {}) {
  let es = null

  function connect() {
    const token = getAccessToken()
    if (!token) return
    const id  = unref(agentId)
    const url = `/v1/agents/${id}/stream?token=${encodeURIComponent(token)}`
    es = new EventSource(url)
    es.addEventListener('agent',     e => onAgent?.(JSON.parse(e.data)))
    es.addEventListener('metrics',   e => onMetrics?.(JSON.parse(e.data)))
    es.addEventListener('processes', e => onProcesses?.(JSON.parse(e.data)))
    es.addEventListener('command',   e => onCommand?.(JSON.parse(e.data)))
    es.addEventListener('ping',      () => {})
    es.onerror = () => {
      es.close()
      es = null
      setTimeout(connect, 3_000)
    }
  }

  onMounted(connect)
  onUnmounted(() => { es?.close(); es = null })
}
