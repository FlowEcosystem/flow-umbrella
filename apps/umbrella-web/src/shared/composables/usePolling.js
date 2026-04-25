export function usePolling(fn, intervalMs = 30_000, { immediate = true } = {}) {
  let timer = null

  function start() {
    if (!timer) timer = setInterval(fn, intervalMs)
  }

  function stop() {
    clearInterval(timer)
    timer = null
  }

  function onVisibility() {
    if (document.hidden) {
      stop()
    } else {
      fn()
      start()
    }
  }

  onMounted(() => {
    if (immediate) fn()
    start()
    document.addEventListener('visibilitychange', onVisibility)
  })

  onUnmounted(() => {
    stop()
    document.removeEventListener('visibilitychange', onVisibility)
  })
}
