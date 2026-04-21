import { formatCalendarDateTime, formatRelativeDate, normalizeOptionalText } from '@/shared/lib/domain-ui'

export const AGENT_STATUS_OPTIONS = Object.freeze([
  { label: 'Ожидает установки', value: 'pending' },
  { label: 'Активен', value: 'active' },
  { label: 'Отключён', value: 'disabled' },
  { label: 'Выведен из эксплуатации', value: 'decommissioned' },
])

export const AGENT_OS_OPTIONS = Object.freeze([
  { label: 'Windows', value: 'windows' },
  { label: 'Linux', value: 'linux' },
  { label: 'macOS', value: 'macos' },
])

export function getAgentStatusLabel(status) {
  return AGENT_STATUS_OPTIONS.find((item) => item.value === status)?.label ?? status
}

export function getAgentOsLabel(os) {
  return AGENT_OS_OPTIONS.find((item) => item.value === os)?.label ?? os
}

export function getAgentStatusClass(status) {
  return `agent-status--${status}`
}

export function formatAgentLastSeen(value) {
  if (!value) return { text: 'Не выходил на связь', muted: true }
  return formatRelativeDate(value)
}

export function formatEnrolledAt(value) {
  if (!value) return 'Не зарегистрирован'
  return formatCalendarDateTime(value)
}

export function buildAgentCreatePayload(form) {
  return {
    hostname: form.hostname.trim(),
    os: form.os,
    notes: normalizeOptionalText(form.notes),
  }
}

export function buildAgentPatch(form, initial) {
  const patch = {}
  const hostname = form.hostname.trim()
  const notes = normalizeOptionalText(form.notes)

  if (hostname !== initial.hostname) patch.hostname = hostname
  if (form.status !== initial.status) patch.status = form.status
  if (notes !== initial.notes) patch.notes = notes

  return patch
}
