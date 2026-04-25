const sessionExpired = ref(false)

export function useSessionExpired() {
  function trigger() { sessionExpired.value = true  }
  function reset()   { sessionExpired.value = false }
  return { sessionExpired, trigger, reset }
}
