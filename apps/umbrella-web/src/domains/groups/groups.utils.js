import { formatCalendarDateTime, normalizeOptionalText } from '@/shared/lib/domain-ui'

export function buildGroupPayload(form) {
  return {
    name: form.name.trim(),
    description: normalizeOptionalText(form.description),
    color: normalizeOptionalText(form.color),
  }
}

export function buildGroupPatch(form, initial) {
  const patch = {}
  const name = form.name.trim()
  const description = normalizeOptionalText(form.description)
  const color = normalizeOptionalText(form.color)

  if (name !== initial.name) patch.name = name
  if (description !== initial.description) patch.description = description
  if (color !== initial.color) patch.color = color

  return patch
}

export function formatGroupUpdatedAt(value) {
  return formatCalendarDateTime(value)
}
