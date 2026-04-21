const relativeTimeFormatter = new Intl.RelativeTimeFormat('ru', { numeric: 'auto' })
const shortMonths = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']

export function normalizeOptionalText(value) {
  const trimmed = value?.trim() ?? ''
  return trimmed ? trimmed : null
}

export function buildValidationState(err, fields) {
  const state = fields.reduce((acc, field) => {
    acc[field] = ''
    return acc
  }, {})

  if (err?.status !== 422) return state

  const missingFields = Array.isArray(err.details?.missing_fields) ? err.details.missing_fields : []
  const invalidFields = Array.isArray(err.details?.invalid_fields) ? err.details.invalid_fields : []

  missingFields.forEach((field) => {
    if (field in state && !state[field]) state[field] = 'Поле обязательно'
  })

  invalidFields.forEach(({ field, message }) => {
    if (field in state && !state[field]) state[field] = message || 'Некорректное значение'
  })

  return state
}

export function formatRelativeDate(value) {
  if (!value) return { text: '—', muted: true }

  const date = new Date(value)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffDays = Math.abs(diffMs) / (1000 * 60 * 60 * 24)

  if (diffDays > 30) {
    return {
      text: `${date.getDate()} ${shortMonths[date.getMonth()]} ${date.getFullYear()}`,
      muted: false,
    }
  }

  const intervals = [
    { unit: 'year', ms: 1000 * 60 * 60 * 24 * 365 },
    { unit: 'month', ms: 1000 * 60 * 60 * 24 * 30 },
    { unit: 'week', ms: 1000 * 60 * 60 * 24 * 7 },
    { unit: 'day', ms: 1000 * 60 * 60 * 24 },
    { unit: 'hour', ms: 1000 * 60 * 60 },
    { unit: 'minute', ms: 1000 * 60 },
  ]

  for (const interval of intervals) {
    if (Math.abs(diffMs) >= interval.ms || interval.unit === 'minute') {
      return { text: relativeTimeFormatter.format(Math.round(diffMs / interval.ms), interval.unit), muted: false }
    }
  }

  return { text: 'только что', muted: false }
}

export function formatCalendarDateTime(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
