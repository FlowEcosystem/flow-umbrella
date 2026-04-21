<script setup>
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'

import { useAdminsStore } from '@/domains/admins/store'
import { ADMIN_ROLE_OPTIONS, buildValidationState, normalizeOptionalText } from '@/domains/admins/admins.utils'

const visible = defineModel('visible', { type: Boolean, default: false })

const emit = defineEmits(['created'])

const toast = useToast()
const adminsStore = useAdminsStore()

const form = reactive({
  email: '',
  password: '',
  full_name: '',
  role: 'admin',
})

const errors = reactive({
  email: '',
  password: '',
  full_name: '',
  role: '',
})

const isSubmitting = ref(false)

function resetForm() {
  form.email = ''
  form.password = ''
  form.full_name = ''
  form.role = 'admin'

  errors.email = ''
  errors.password = ''
  errors.full_name = ''
  errors.role = ''
}

function clearFieldError(field) {
  errors[field] = ''
}

function applyValidation(err) {
  const nextErrors = buildValidationState(err, ['email', 'password', 'full_name', 'role'])
  Object.assign(errors, nextErrors)
}

async function submit() {
  if (isSubmitting.value) return

  isSubmitting.value = true
  Object.assign(errors, { email: '', password: '', full_name: '', role: '' })

  try {
    const payload = {
      email: form.email.trim(),
      password: form.password,
      full_name: normalizeOptionalText(form.full_name),
      role: form.role,
    }

    const admin = await adminsStore.create(payload)
    emit('created', admin)
    visible.value = false
    resetForm()
    toast.add({ severity: 'success', summary: 'Администратор создан', life: 3000 })
  } catch (err) {
    if (err.status === 409 && err.error_code === 'admin_email_already_exists') {
      errors.email = 'Email уже используется'
      return
    }

    if (err.status === 422) {
      applyValidation(err)
      return
    }

    toast.add({ severity: err.status === 403 ? 'warn' : 'error', summary: err.message, life: 4000 })
  } finally {
    isSubmitting.value = false
  }
}

watch(visible, (value) => {
  if (value) {
    resetForm()
    return
  }

  isSubmitting.value = false
})
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Новый администратор"
    :closable="!isSubmitting"
    :style="{ width: '480px', maxWidth: 'calc(100vw - 32px)' }"
  >
    <div class="admin-modal__body">
      <div class="field">
        <label class="field-label" for="admin-create-email">Email</label>
        <InputText
          id="admin-create-email"
          v-model="form.email"
          type="email"
          placeholder="admin@example.com"
          autocomplete="email"
          :invalid="!!errors.email"
          autofocus
          fluid
          @update:model-value="clearFieldError('email')"
        />
        <small v-if="errors.email" class="field-error">{{ errors.email }}</small>
      </div>

      <div class="field">
        <label class="field-label" for="admin-create-password">Пароль</label>
        <Password
          id="admin-create-password"
          v-model="form.password"
          placeholder="Минимум 8 символов"
          :feedback="false"
          toggleMask
          maxlength="72"
          autocomplete="new-password"
          :invalid="!!errors.password"
          fluid
          @update:model-value="clearFieldError('password')"
        />
        <small v-if="errors.password" class="field-error">{{ errors.password }}</small>
      </div>

      <div class="field">
        <label class="field-label" for="admin-create-full-name">Полное имя</label>
        <InputText
          id="admin-create-full-name"
          v-model="form.full_name"
          placeholder="Иван Иванов"
          maxlength="255"
          :invalid="!!errors.full_name"
          fluid
          @update:model-value="clearFieldError('full_name')"
        />
        <small v-if="errors.full_name" class="field-error">{{ errors.full_name }}</small>
      </div>

      <div class="field">
        <label class="field-label" for="admin-create-role">Роль</label>
        <Select
          id="admin-create-role"
          v-model="form.role"
          :options="ADMIN_ROLE_OPTIONS"
          option-label="label"
          option-value="value"
          placeholder="Выберите роль"
          :invalid="!!errors.role"
          fluid
          @update:model-value="clearFieldError('role')"
        />
        <small v-if="errors.role" class="field-error">{{ errors.role }}</small>
      </div>
    </div>

    <template #footer>
      <div class="admin-modal__footer">
        <Button label="Отмена" severity="secondary" outlined :disabled="isSubmitting" @click="visible = false" />
        <Button label="Создать" :loading="isSubmitting" :disabled="isSubmitting" @click="submit" />
      </div>
    </template>
  </Dialog>
</template>

<style scoped>
.admin-modal__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.admin-modal__footer {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.field-error {
  font-size: var(--text-xs);
  color: var(--color-danger);
}
</style>
