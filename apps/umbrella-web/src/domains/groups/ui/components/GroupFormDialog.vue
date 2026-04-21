<script setup>
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'

const props = defineProps({
  mode: {
    type: String,
    default: 'create',
  },
  form: {
    type: Object,
    required: true,
  },
  errors: {
    type: Object,
    required: true,
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
  isUnchanged: {
    type: Boolean,
    default: false,
  },
  onSubmit: {
    type: Function,
    required: true,
  },
  onClearError: {
    type: Function,
    required: true,
  },
})

const visible = defineModel('visible', { type: Boolean, default: false })

const dialogTitle = computed(() => (props.mode === 'edit' ? 'Редактировать группу' : 'Новая группа'))
const submitLabel = computed(() => (props.mode === 'edit' ? 'Сохранить' : 'Создать'))
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="dialogTitle"
    :closable="!isSubmitting"
    :style="{ width: '520px', maxWidth: 'calc(100vw - 32px)' }"
  >
    <div class="dialog-body">
      <div class="field">
        <label class="field-label" :for="`${mode}-group-name`">Название</label>
        <InputText
          :id="`${mode}-group-name`"
          v-model="form.name"
          :invalid="!!errors.name"
          :placeholder="mode === 'create' ? 'Production' : ''"
          fluid
          :autofocus="mode === 'create'"
          @update:model-value="onClearError('name')"
        />
        <small v-if="errors.name" class="field-error">{{ errors.name }}</small>
      </div>

      <div class="field">
        <label class="field-label" :for="`${mode}-group-description`">Описание</label>
        <Textarea
          :id="`${mode}-group-description`"
          v-model="form.description"
          rows="4"
          auto-resize
          :invalid="!!errors.description"
          placeholder="Краткое описание назначения группы"
          fluid
          @update:model-value="onClearError('description')"
        />
        <small v-if="errors.description" class="field-error">{{ errors.description }}</small>
      </div>

      <div class="field">
        <label class="field-label" :for="`${mode}-group-color`">Цвет</label>
        <div class="color-field">
          <input v-model="form.color" type="color" class="color-picker" />
          <InputText
            :id="`${mode}-group-color`"
            v-model="form.color"
            :invalid="!!errors.color"
            placeholder="#c17f59"
            fluid
            @update:model-value="onClearError('color')"
          />
        </div>
        <small v-if="errors.color" class="field-error">{{ errors.color }}</small>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <Button label="Отмена" severity="secondary" outlined :disabled="isSubmitting" @click="visible = false" />
        <Button
          :label="submitLabel"
          :loading="isSubmitting"
          :disabled="isSubmitting || (mode === 'edit' && isUnchanged)"
          @click="onSubmit"
        />
      </div>
    </template>
  </Dialog>
</template>
