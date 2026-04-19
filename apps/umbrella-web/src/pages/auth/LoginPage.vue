<script setup>
import { useAuthStore } from '@/stores/auth.store'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const formError = ref('')
const fieldErrors = ref({})

async function handleSubmit() {
  formError.value = ''
  fieldErrors.value = {}
  try {
    await authStore.login(email.value, password.value)
    router.push(route.query.redirect || '/')
  } catch (err) {
    formError.value = err.message ?? 'Не удалось выполнить вход'
    if (err.details?.invalid_fields) {
      err.details.invalid_fields.forEach((f) => {
        fieldErrors.value[f.field] = f.message
      })
    }
    if (err.details?.missing_fields) {
      err.details.missing_fields.forEach((f) => {
        if (!fieldErrors.value[f]) fieldErrors.value[f] = 'Поле обязательно'
      })
    }
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-panel">
      <div class="login-brand">
        <div class="login-brand-lockup">
          <span class="login-brand-mark">
            <Shield class="icon-xl" />
          </span>
          <h1 class="login-title">Umbrella</h1>
        </div>
        <p class="login-subtitle">Сдержанный контур управления конечными устройствами</p>
      </div>

      <div class="login-card">
        <form class="login-form" @submit.prevent="handleSubmit">
          <Message v-if="formError" severity="error">{{ formError }}</Message>

          <div class="field">
            <label for="login-email" class="field-label">Почта</label>
            <InputText
              class="field-control"
              id="login-email"
              v-model="email"
              type="email"
              autocomplete="email"
              :invalid="!!fieldErrors.email"
              fluid
              placeholder="name@company.com"
            />
            <small v-if="fieldErrors.email" class="field-error">{{ fieldErrors.email }}</small>
          </div>

          <div class="field">
            <label for="login-password" class="field-label">Пароль</label>
            <Password
              class="field-control"
              id="login-password"
              v-model="password"
              :feedback="false"
              :invalid="!!fieldErrors.password"
              toggleMask
              fluid
              placeholder="Введите пароль"
            />
            <small v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</small>
          </div>

          <Button
            class="login-submit"
            type="submit"
            label="Войти"
            size="large"
            :loading="authStore.isLoading"
            :disabled="authStore.isLoading"
            fluid
          />
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: var(--color-bg);
}

.login-panel {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.login-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.login-brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.login-brand-mark {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
}

.login-title {
  color: var(--color-text);
  font-family: var(--font-serif);
  font-size: 44px;
  font-weight: 400;
  line-height: 1;
  letter-spacing: -0.03em;
}

.login-subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  text-align: center;
  line-height: var(--leading-normal);
}

.login-card {
  padding: 28px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.login-form,
.field {
  display: flex;
  flex-direction: column;
}

.login-form {
  gap: 16px;
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

.login-submit {
  margin-top: 8px;
}

@media (max-width: 767px) {
  .login-page {
    padding: 20px 16px;
    align-items: flex-start;
    padding-top: 80px;
  }

  .login-title {
    font-size: 36px;
  }

  .login-card {
    padding: 20px;
  }
}
</style>
