export function useBreadcrumbs() {
  const route = useRoute()

  const crumbs = computed(() => {
    const matched = route.matched || []

    return matched
      .map((r) => {
        const bc = r.meta?.crumb
        if (!bc) return null

        const label = typeof bc === 'function' ? bc(route) : bc

        return {
          label,
          icon: r.meta?.icon ?? null,
          to: r.name ? { name: r.name, params: route.params } : r.path,
        }
      })
      .filter(Boolean)
  })

  return { crumbs }
}
