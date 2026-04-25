export function usePagination(items, perPage = 24) {
  const page = ref(1)
  const limit = typeof perPage === 'number' ? perPage : perPage

  const totalPages = computed(() => Math.max(1, Math.ceil(items.value.length / limit)))

  const paged = computed(() => {
    const start = (page.value - 1) * limit
    return items.value.slice(start, start + limit)
  })

  watch(items, () => { page.value = 1 })

  function goTo(n) {
    page.value = Math.max(1, Math.min(n, totalPages.value))
  }

  return { page, totalPages, paged, goTo }
}
