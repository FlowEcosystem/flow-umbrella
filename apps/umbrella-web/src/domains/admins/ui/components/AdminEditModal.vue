<script setup>
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'

import UiTooltip from '@/shared/ui/UiTooltip.vue'
import { ADMIN_ROLE_OPTIONS, buildValidationState, normalizeOptionalText } from '@/domains/admins/admins.utils'

const props = defineProps({
  admin: {
    type: Object,
    default: null,
  },
  onSubmit: {
    type: Function,
    required: true,
  },
  currentUserId: {
    type: String,
    default: null,
  },
})

const visible = defineModel('visible', { type: Boolean, default: false })

const emit = defineEmits(['updated'])

const toast = useToast()

const form = reactive({
  email: '',
  full_name: '',
  role: 'admin',
  is_active: true,
})

const errors = reactive({
  email: '',
  full_name: '',
  role: '',
  is_active: '',
})

const isSubmitting = ref(false)

const isSelf = computed(() => props.admin?.id && props.admin.id === props.currentUserId)

const normalizedInitial = computed(() => ({
  email: props.admin?.email ?? '',
  full_name: normalizeOptionalText(props.admin?.full_name),
  role: props.admin?.role ?? 'admin',
  is_active: props.admin?.is_active ?? true,
}))

const patchPayload = computed(() => {
  if (!props.admin) return {}

  const patch = {}
  const email = form.email.trim()
  const fullName = normalizeOptionalText(form.full_name)

  if (email !== normalizedInitial.value.email) patch.email = email
  if (fullName !== normalizedInitial.value.full_name) patch.full_name = fullName
  if (!isSelf.value && form.role !== normalizedInitial.value.role) patch.role = form.role
  if (!isSelf.value && form.is_active !== normalizedInitial.value.is_active) patch.is_active = form.is_active

  return patch
})

const isUnchanged = computed(() => Object.keys(patchPayload.value).length === 0)

function syncForm() {
  form.email = props.admin?.email ?? ''
  form.full_name = props.admin?.full_name ?? ''
  form.role = props.admin?.role ?? 'admin'
  form.is_active = props.admin?.is_active ?? true

  errors.email = ''
  errors.full_name = ''
  errors.role = ''
  errors.is_active = ''
}

function clearFieldError(field) {
  errors[field] = ''
}

function applyValidation(err) {
  const nextErrors = buildValidationState(err, ['email', 'full_name', 'role', 'is_active'])
  Object.assign(errors, nextErrors)
}

async function submit() {
  if (isSubmitting.value || isUnchanged.value || !props.admin) return

  isSubmitting.value = true
  Object.assign(errors, { email: '', full_name: '', role: '', is_active: '' })

  try {
    const updated = await props.onSubmit(props.admin.id, patchPayload.value)
    emit('updated', updated)
    visible.value = false
    toast.add({ severity: 'success', summary: 'Изменения сохранены', life: 3000 })
  } catch (err) {
    if (err.status === 409 && err.error_code === 'admin_email_already_exists') {
      errors.email = 'Email уже используется'
      return
    }

    if (err.status === 409) {
      toast.add({ severity: 'warn', summary: err.message, life: 4500 })
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

watch(
  () => [visible.value, props.admin],
  ([nextVisible]) => {
    if (nextVisible) syncForm()
  },
  { immediate: true },
)
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Редактировать администратора"
    :closable="!isSubmitting"
    :style="{ width: '480px', maxWidth: 'calc(100vw - 32px)' }"
  >
    <div class="admin-modal__body">
      <div class="field">
        <label class="field-label" for="admin-edit-email">Email</label>
        <InputText
          id="admin-edit-email"
          v-model="form.email"
          type="email"
          placeholder="admin@example.com"
          autocomplete="email"
          :invalid="!!errors.email"
          fluid
          @update:model-value="clearFieldError('email')"
        />
        <small v-if="errors.email" class="field-error">{{ errors.email }}</small>
      </div>

      <div class="field">
        <label class="field-label" for="admin-edit-full-name">Полное имя</label>
        <InputText
          id="admin-edit-full-name"
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
        <label class="field-label" for="admin-edit-role">Роль</label>
        <UiTooltip v-if="isSelf" text="Нельзя изменить свою роль">
          <div class="field-tooltip-wrap">
            <Select
              id="admin-edit-role"
              v-model="form.role"
              :options="ADMIN_ROLE_OPTIONS"
              option-label="label"
              option-value="value"
              disabled
              fluid
            />
          </div>
        </UiTooltip>
        <Select
          v-else
          id="admin-edit-role"
          v-model="form.role"
          :options="ADMIN_ROLE_OPTIONS"
          option-label="label"
          option-value="value"
          :invalid="!!errors.role"
          fluid
          @update:model-value="clearFieldError('role')"
        />
        <small v-if="errors.role" class="field-error">{{ errors.role }}</small>
      </div>

      <div class="field">
        <span class="field-label">Статус</span>
        <UiTooltip v-if="isSelf" text="Нельзя деактивировать себя">
          <div class="toggle-field is-disabled">
            <ToggleSwitch v-model="form.is_active" disabled />
            <span class="toggle-label">Активный аккаунт</span>
          </div>
        </UiTooltip>
        <label v-else class="toggle-field">
          <ToggleSwitch v-model="form.is_active" @update:model-value="clearFieldError('is_active')" />
          <span class="toggle-label">Активный аккаунт</span>
        </label>
        <small v-if="errors.is_active" class="field-error">{{ errors.is_active }}</small>
      </div>
    </div>

    <template #footer>
      <div class="admin-modal__footer">
        <Button label="Отмена" severity="secondary" outlined :disabled="isSubmitting" @click="visible = false" />
        <Button label="Сохранить" :loading="isSubmitting" :disabled="isSubmitting || isUnchanged" @click="submit" />
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

.field-tooltip-wrap {
  width: 100%;
}

.toggle-field {
  min-height: 48px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text);
}

.toggle-field.is-disabled {
  cursor: not-allowed;
}

.toggle-label {
  font-size: var(--text-sm);
}
</style>
