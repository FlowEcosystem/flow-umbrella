export const COLOR_PRESETS = [
  '#e05c3a', '#d4785a', '#e0943a', '#d4b45a',
  '#5a9e6e', '#3a8cb4', '#5a6eb4', '#9e5ab4',
  '#b45a8c', '#6e6e6e', '#3ab4a0', '#8cb45a',
]

export function colorToStyle(color) {
  if (!color) return {}
  return { backgroundColor: color + '22', borderColor: color + '66' }
}

export function colorDotStyle(color) {
  if (!color) return {}
  return { backgroundColor: color }
}

export function fallbackColor(name) {
  if (!name) return '#6e6e6e'
  const idx = name.charCodeAt(0) % COLOR_PRESETS.length
  return COLOR_PRESETS[idx]
}
