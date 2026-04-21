<script setup>
import { useToast } from 'primevue/usetoast'
import { getRoleLabel } from '@/app/access/rbac'
import { useAuthStore } from '@/domains/auth/store'

const authStore = useAuthStore()
const router = useRouter()
const toast = useToast()

const user = computed(() => authStore.currentUser)

// ─── Profile ────────────────────────────────────────────────────────────────

const profileForm = reactive({ full_name: '', avatar_url: '' })
const profileInitial = reactive({ full_name: '', avatar_url: '' })
const profileSaving = ref(false)
const profileAvatarError = ref(false)

watch(
  user,
  (u) => {
    profileForm.full_name = u?.full_name ?? ''
    profileForm.avatar_url = u?.avatar_url ?? ''
    Object.assign(profileInitial, profileForm)
    profileAvatarError.value = false
  },
  { immediate: true },
)

watch(
  () => profileForm.avatar_url,
  () => { profileAvatarError.value = false },
)

const profileChanged = computed(
  () =>
    profileForm.full_name !== profileInitial.full_name ||
    profileForm.avatar_url !== profileInitial.avatar_url,
)

const profileInitials = computed(() => {
  const src = profileForm.full_name || user.value?.email || ''
  return src
    .split(/[\s@]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
})

const showProfileAvatar = computed(() => profileForm.avatar_url && !profileAvatarError.value)

async function saveProfile() {
  if (!profileChanged.value || profileSaving.value) return
  profileSaving.value = true
  try {
    const patch = {}
    if (profileForm.full_name !== profileInitial.full_name) patch.full_name = profileForm.full_name
    if (profileForm.avatar_url !== profileInitial.avatar_url) patch.avatar_url = profileForm.avatar_url
    await authStore.updateProfile(patch)
    toast.add({ severity: 'success', summary: 'Профиль обновлён', life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Не удалось сохранить профиль', life: 4000 })
  } finally {
    profileSaving.value = false
  }
}

// ─── Account ────────────────────────────────────────────────────────────────

const roleLabel = computed(() => getRoleLabel(user.value?.role))

const lastLoginFormatted = computed(() => {
  if (!user.value?.last_login_at) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(user.value.last_login_at))
})

// ─── Security ───────────────────────────────────────────────────────────────

const secForm = reactive({ current: '', next: '', confirm: '' })
const secErrors = reactive({ current: '', next: '', confirm: '' })
const secSaving = ref(false)

function clearSecErrors() {
  secErrors.current = ''
  secErrors.next = ''
  secErrors.confirm = ''
}

const secValid = computed(() => {
  const { current, next, confirm } = secForm
  return current.length > 0 && next.length >= 8 && next === confirm && next !== current
})

async function submitPassword() {
  if (!secValid.value || secSaving.value) return
  clearSecErrors()
  secSaving.value = true
  try {
    await authStore.changePassword(secForm.current, secForm.next)
    toast.add({ severity: 'success', summary: 'Пароль изменён, выполняется выход…', life: 3000 })
    setTimeout(async () => {
      await authStore.logout()
      router.push('/login')
    }, 1500)
  } catch (err) {
    if (err.status === 401 && err.error_code === 'invalid_credentials') {
      secErrors.current = 'Неверный текущий пароль'
    } else if (err.status === 422) {
      const fieldMap = { current_password: 'current', new_password: 'next' }
      const errors = err.details?.errors ?? []
      errors.forEach(({ field, message }) => {
        const key = fieldMap[field]
        if (key) secErrors[key] = message
      })
    } else {
      toast.add({ severity: 'error', summary: 'Не удалось изменить пароль', life: 4000 })
    }
    secSaving.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <h1 class="page-title">Настройки</h1>
      <p class="page-subtitle">Параметры аккаунта и безопасности.</p>
    </div>

    <!-- Profile -->
    <section class="settings-section">
      <h2 class="section-title">Профиль</h2>
      <Card>
        <template #content>
          <div class="profile-editor">
            <div class="profile-avatar-wrap">
              <img
                v-if="showProfileAvatar"
                :src="profileForm.avatar_url"
                alt="avatar"
                class="profile-avatar-img"
                @error="profileAvatarError = true"
              />
              <span v-else class="profile-avatar-fallback">{{ profileInitials || '?' }}</span>
            </div>

            <div class="profile-fields">
              <div class="field">
                <label class="field-label" for="full_name">Полное имя</label>
                <InputText
                  id="full_name"
                  v-model="profileForm.full_name"
                  class="field-control"
                  placeholder="Введите имя"
                  fluid
                />
              </div>
              <div class="field">
                <label class="field-label" for="avatar_url">URL аватара</label>
                <InputText
                  id="avatar_url"
                  v-model="profileForm.avatar_url"
                  class="field-control"
                  placeholder="https://…"
                  maxlength="2048"
                  fluid
                />
              </div>
              <div class="field-actions">
                <Button
                  label="Сохранить"
                  :disabled="!profileChanged || profileSaving"
                  :loading="profileSaving"
                  @click="saveProfile"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>
    </section>

    <!-- Account -->
    <section class="settings-section">
      <h2 class="section-title">Аккаунт</h2>
      <Card>
        <template #content>
          <div class="account-rows">
            <div class="account-row">
              <span class="account-row-label">Email</span>
              <span class="account-row-value">{{ user?.email }}</span>
            </div>
            <div class="account-row">
              <span class="account-row-label">Роль</span>
              <span class="role-badge">{{ roleLabel }}</span>
            </div>
            <div class="account-row">
              <span class="account-row-label">Последний вход</span>
              <span class="account-row-value">{{ lastLoginFormatted }}</span>
            </div>
          </div>
          <p class="account-hint">Для изменения email или роли обратитесь к суперадминистратору.</p>
        </template>
      </Card>
    </section>

    <!-- Security -->
    <section class="settings-section">
      <h2 class="section-title">Безопасность</h2>
      <Card>
        <template #content>
          <div class="security-fields">
            <div class="field">
              <label class="field-label" for="current_password">Текущий пароль</label>
              <Password
                id="current_password"
                v-model="secForm.current"
                class="field-control"
                :feedback="false"
                toggleMask
                placeholder="Введите текущий пароль"
                :invalid="!!secErrors.current"
                fluid
              />
              <small v-if="secErrors.current" class="field-error">{{ secErrors.current }}</small>
            </div>
            <div class="field">
              <label class="field-label" for="new_password">Новый пароль</label>
              <Password
                id="new_password"
                v-model="secForm.next"
                class="field-control"
                :feedback="false"
                toggleMask
                placeholder="Минимум 8 символов"
                :invalid="!!secErrors.next"
                fluid
              />
              <small v-if="secErrors.next" class="field-error">{{ secErrors.next }}</small>
            </div>
            <div class="field">
              <label class="field-label" for="confirm_password">Повтор пароля</label>
              <Password
                id="confirm_password"
                v-model="secForm.confirm"
                class="field-control"
                :feedback="false"
                toggleMask
                placeholder="Повторите новый пароль"
                :invalid="!!secErrors.confirm"
                fluid
              />
              <small v-if="secErrors.confirm" class="field-error">{{ secErrors.confirm }}</small>
            </div>
            <div class="field-actions">
              <Button
                label="Изменить пароль"
                severity="secondary"
                :disabled="!secValid || secSaving"
                :loading="secSaving"
                @click="submitPassword"
              />
            </div>
          </div>
        </template>
      </Card>
    </section>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.settings-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.page-title {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 400;
  line-height: 1.08;
  letter-spacing: -0.025em;
}

.page-subtitle {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

/* Profile editor */
.profile-editor {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.profile-avatar-wrap {
  flex-shrink: 0;
  width: 72px;
  height: 72px;
}

.profile-avatar-img {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.profile-avatar-fallback {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-size: var(--text-xl);
  font-weight: 600;
  letter-spacing: -0.02em;
}

.profile-fields {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Shared field styles */
.field {
  display: flex;
  flex-direction: column;
}

.field-label {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.field-control {
  margin-top: 8px;
}

.field-error {
  margin-top: 6px;
  color: var(--color-danger);
  font-size: var(--text-xs);
}

.field-actions {
  display: flex;
  padding-top: 4px;
}

/* Account rows */
.account-rows {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.account-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.account-row-label {
  width: 140px;
  flex-shrink: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.account-row-value {
  font-size: var(--text-sm);
  color: var(--color-text);
}

.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.account-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

/* Security */
.security-fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 440px;
}
</style>
