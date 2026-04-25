export const OS_LABELS = {
  windows: 'Windows',
  linux:   'Linux',
  macos:   'macOS',
}

export const STATUS_LABELS = {
  pending:        'Ожидание',
  active:         'Активен',
  disabled:       'Отключён',
  decommissioned: 'Выведен',
}

export const STATUS_CLASSES = {
  pending:        'border-amber-900/40 bg-amber-950/50 text-amber-400',
  active:         'border-emerald-900/40 bg-emerald-950/50 text-emerald-400',
  disabled:       'border-white/10 bg-white/5 text-fg-subtle',
  decommissioned: 'border-red-900/40 bg-red-950/50 text-red-400',
}

export const STATUS_DOT = {
  pending:        'bg-amber-400',
  active:         'bg-emerald-400',
  disabled:       'bg-fg-subtle',
  decommissioned: 'bg-red-400',
}

export const AGENT_STATUSES = ['pending', 'active', 'disabled', 'decommissioned']
export const AGENT_OS_LIST  = ['windows', 'linux', 'macos']

export function formatLastSeen(dateStr) {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins  = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days  = Math.floor(diff / 86_400_000)
  if (mins < 1)   return 'только что'
  if (mins < 60)  return `${mins} мин. назад`
  if (hours < 24) return `${hours} ч. назад`
  return `${days} дн. назад`
}

export function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}
