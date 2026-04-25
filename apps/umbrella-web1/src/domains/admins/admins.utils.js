export const ROLE_LABELS = {
  superadmin: 'Суперадмин',
  admin:      'Администратор',
  viewer:     'Наблюдатель',
}

export const ROLE_CLASSES = {
  superadmin: 'border-amber-800/40 bg-amber-950/40 text-amber-400',
  admin:      'border-accent/30 bg-accent/10 text-accent',
  viewer:     'border-white/[0.08] bg-white/[0.03] text-fg-subtle',
}

export const ADMIN_ROLES = ['superadmin', 'admin', 'viewer']

export function formatLastLogin(dateStr) {
  if (!dateStr) return 'Никогда'
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1)   return 'Только что'
  if (m < 60)  return `${m} мин назад`
  const h = Math.floor(m / 60)
  if (h < 24)  return `${h} ч назад`
  const d = Math.floor(h / 24)
  if (d < 7)   return `${d} д назад`
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}
