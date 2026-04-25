const toasts = ref([])
let _id = 0

export function useToast() {
  function add({ type = 'success', message, duration = 4000 }) {
    const id = _id++
    toasts.value.push({ id, type, message })
    if (duration > 0) setTimeout(() => remove(id), duration)
    return id
  }

  function remove(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (message) => add({ type: 'success', message })
  const error   = (message) => add({ type: 'error',   message, duration: 6000 })
  const warning = (message) => add({ type: 'warning', message })

  return { toasts, success, error, warning, remove }
}
