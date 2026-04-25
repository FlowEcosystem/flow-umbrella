import { useAgentsStore }   from '@/domains/agents/store'
import { useGroupsStore }   from '@/domains/groups/store'
import { usePoliciesStore } from '@/domains/policies/store'
import { useServicesStore } from '@/domains/policies/servicesStore'
import { useAuthStore }     from '@/domains/auth/store'

export function useDashboardPage() {
  const agentsStore   = useAgentsStore()
  const groupsStore   = useGroupsStore()
  const policiesStore = usePoliciesStore()
  const servicesStore = useServicesStore()
  const auth          = useAuthStore()

  onMounted(() => {
    if (!agentsStore.items.length)   agentsStore.fetch()
    if (!groupsStore.items.length)   groupsStore.fetch()
    if (!policiesStore.items.length) policiesStore.fetch()
    if (!servicesStore.items.length) servicesStore.fetch()
  })

  // ── agent stats ───────────────────────────────────────────
  const totalAgents  = computed(() => agentsStore.items.length)
  const activeAgents = computed(() => agentsStore.items.filter(a => a.status === 'active').length)

  const byStatus = computed(() => {
    const counts = { active: 0, pending: 0, disabled: 0, decommissioned: 0 }
    agentsStore.items.forEach(a => { if (a.status in counts) counts[a.status]++ })
    return counts
  })

  const byOs = computed(() => {
    const counts = { windows: 0, linux: 0, macos: 0 }
    agentsStore.items.forEach(a => { if (a.os in counts) counts[a.os]++ })
    return counts
  })

  const statusBars = computed(() => {
    const total = totalAgents.value || 1
    return [
      { key: 'active',         label: 'Активны',   color: 'bg-emerald-400', dot: 'bg-emerald-400', count: byStatus.value.active },
      { key: 'pending',        label: 'Ожидание',  color: 'bg-amber-400',   dot: 'bg-amber-400',   count: byStatus.value.pending },
      { key: 'disabled',       label: 'Отключены', color: 'bg-white/25',    dot: 'bg-white/25',    count: byStatus.value.disabled },
      { key: 'decommissioned', label: 'Выведены',  color: 'bg-red-400',     dot: 'bg-red-400',     count: byStatus.value.decommissioned },
    ].map(s => ({ ...s, pct: Math.round((s.count / total) * 100) }))
  })

  const osBars = computed(() => {
    const total = totalAgents.value || 1
    return [
      { key: 'windows', label: 'Windows', color: 'bg-sky-400',    count: byOs.value.windows },
      { key: 'linux',   label: 'Linux',   color: 'bg-violet-400', count: byOs.value.linux },
      { key: 'macos',   label: 'macOS',   color: 'bg-rose-400',   count: byOs.value.macos },
    ].map(o => ({ ...o, pct: Math.round((o.count / total) * 100) }))
  })

  // ── policy stats ──────────────────────────────────────────
  const totalPolicies    = computed(() => policiesStore.items.length)
  const activePolicies   = computed(() => policiesStore.items.filter(p => p.is_active).length)
  const inactivePolicies = computed(() => totalPolicies.value - activePolicies.value)
  const blockPolicies    = computed(() => policiesStore.items.filter(p => p.action === 'block').length)
  const allowPolicies    = computed(() => policiesStore.items.filter(p => p.action === 'allow').length)

  // ── services stats ────────────────────────────────────────
  const totalServices = computed(() => servicesStore.items.length)

  // ── recent agents ─────────────────────────────────────────
  const recentAgents = computed(() =>
    [...agentsStore.items]
      .filter(a => a.last_seen_at)
      .sort((a, b) => new Date(b.last_seen_at) - new Date(a.last_seen_at))
      .slice(0, 8)
  )

  // ── top groups ────────────────────────────────────────────
  const topGroups = computed(() =>
    [...groupsStore.items]
      .sort((a, b) => (b.agents_count ?? 0) - (a.agents_count ?? 0))
      .slice(0, 6)
  )

  // ── greeting ──────────────────────────────────────────────
  const greeting = computed(() => {
    const h    = new Date().getHours()
    const name = auth.currentUser?.full_name?.split(' ')[0] ?? ''
    const base = h < 6 ? 'Доброй ночи' : h < 12 ? 'Доброе утро' : h < 18 ? 'Добрый день' : 'Добрый вечер'
    return name ? `${base}, ${name}` : base
  })

  const todayDate = computed(() =>
    new Date().toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
  )

  return {
    agentsStore, groupsStore, policiesStore, servicesStore,
    totalAgents, activeAgents, statusBars, osBars,
    totalPolicies, activePolicies, inactivePolicies, blockPolicies, allowPolicies,
    totalServices,
    recentAgents, topGroups,
    greeting, todayDate,
  }
}
