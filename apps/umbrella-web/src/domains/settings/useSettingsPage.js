import { useAuthStore } from '@/domains/auth/store'
import { useToast }     from '@/shared/composables/useToast'

const ROLE_LABELS = {
  superadmin: 'Суперадмин',
  admin:      'Администратор',
  viewer:     'Наблюдатель',
}

export function useSettingsPage() {
  const auth  = useAuthStore()
  const toast = useToast()

  // ── profile ───────────────────────────────────────────────
  const profileForm    = ref({ full_name: '', avatar_url: '' })
  const profileLoading = ref(false)
  const profileError   = ref('')
  const profileSuccess = ref(false)

  watch(
    () => auth.currentUser,
    (user) => {
      if (user) {
        profileForm.value = {
          full_name:  user.full_name  ?? '',
          avatar_url: user.avatar_url ?? '',
        }
      }
    },
    { immediate: true },
  )

  const profileDirty = computed(() => {
    const u = auth.currentUser
    if (!u) return false
    return (
      profileForm.value.full_name  !== (u.full_name  ?? '') ||
      profileForm.value.avatar_url !== (u.avatar_url ?? '')
    )
  })

  async function submitProfile() {
    profileLoading.value = true
    profileError.value   = ''
    profileSuccess.value = false
    try {
      await auth.updateProfile({
        full_name:  profileForm.value.full_name  || null,
        avatar_url: profileForm.value.avatar_url || null,
      })
      profileSuccess.value = true
      toast.success('Профиль сохранён')
      setTimeout(() => { profileSuccess.value = false }, 3000)
    } catch (err) {
      profileError.value = err.message ?? 'Ошибка сохранения'
      toast.error(profileError.value)
    } finally {
      profileLoading.value = false
    }
  }

  // ── password ──────────────────────────────────────────────
  const passwordForm    = ref({ current: '', next: '', confirm: '' })
  const passwordLoading = ref(false)
  const passwordError   = ref('')
  const passwordSuccess = ref(false)

  const passwordMismatch = computed(() =>
    passwordForm.value.next &&
    passwordForm.value.confirm &&
    passwordForm.value.next !== passwordForm.value.confirm
  )

  const passwordValid = computed(() =>
    passwordForm.value.current.length >= 1 &&
    passwordForm.value.next.length    >= 8 &&
    passwordForm.value.next === passwordForm.value.confirm
  )

  async function submitPassword() {
    if (!passwordValid.value) return
    passwordLoading.value = true
    passwordError.value   = ''
    passwordSuccess.value = false
    try {
      await auth.changePassword(passwordForm.value.current, passwordForm.value.next)
      passwordForm.value    = { current: '', next: '', confirm: '' }
      passwordSuccess.value = true
      toast.success('Пароль изменён')
      setTimeout(() => { passwordSuccess.value = false }, 3000)
    } catch (err) {
      passwordError.value = err.message ?? 'Ошибка смены пароля'
      toast.error(passwordError.value)
    } finally {
      passwordLoading.value = false
    }
  }

  return {
    auth,
    ROLE_LABELS,
    profileForm, profileLoading, profileError, profileSuccess, profileDirty, submitProfile,
    passwordForm, passwordLoading, passwordError, passwordSuccess,
    passwordMismatch, passwordValid, submitPassword,
  }
}
