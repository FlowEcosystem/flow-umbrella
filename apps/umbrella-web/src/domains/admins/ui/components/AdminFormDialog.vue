<script setup>
import { X } from 'lucide-vue-next'
import { ROLE_LABELS, ADMIN_ROLES } from '@/domains/admins/admins.utils'

const props = defineProps({
  open:    { type: Boolean, required: true },
  form:    { type: Object,  required: true },
  isEdit:  { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: '' },
})

defineEmits(['update:open', 'submit'])

const title = computed(() => props.isEdit ? 'Редактировать админа' : 'Новый администратор')

const canSubmit = computed(() => {
  if (props.isEdit) return !!props.form.email
  return !!props.form.email && props.form.password?.length >= 8
})
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent
      :show-close-button="false"
      aria-describedby="undefined"
      class="max-w-[460px] p-0 border-white/[0.08] bg-bg-raised gap-0"
    >
      <!-- header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4">
        <DialogTitle class="text-base font-medium text-fg">{{ title }}</DialogTitle>
        <button @click="$emit('update:open', false)" :disabled="loading"
                class="text-fg-subtle hover:text-fg transition-colors disabled:opacity-40">
          <X :size="16" />
        </button>
      </div>

      <div class="h-px bg-white/[0.06] mx-6" />

      <!-- body -->
      <div class="px-6 py-5 flex flex-col gap-4">

        <!-- email -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Email</label>
          <input
            v-model="form.email"
            type="email"
            placeholder="admin@company.com"
            :disabled="isEdit"
            class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20
                   transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        <!-- password (create only) -->
        <div v-if="!isEdit" class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Пароль <span class="opacity-40">(мин. 8 символов)</span></label>
          <input
            v-model="form.password"
            type="password"
            autocomplete="new-password"
            class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>

        <!-- full_name -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Имя <span class="opacity-40">(необязательно)</span></label>
          <input
            v-model="form.full_name"
            placeholder="Иван Иванов"
            class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>

        <!-- role -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Роль</label>
          <div class="flex gap-1.5">
            <button
              v-for="r in ADMIN_ROLES" :key="r"
              type="button"
              @click="form.role = r"
              class="h-8 px-3 rounded-md text-xs border transition-all duration-100"
              :class="form.role === r
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
            >
              {{ ROLE_LABELS[r] }}
            </button>
          </div>
        </div>

        <!-- is_active (edit only) -->
        <div v-if="isEdit" class="flex items-center justify-between py-1">
          <div>
            <p class="text-sm text-fg">Активен</p>
            <p class="text-xs text-fg-subtle/60">Неактивный не может войти в систему</p>
          </div>
          <button
            type="button"
            @click="form.is_active = !form.is_active"
            class="relative w-9 h-5 rounded-full transition-colors duration-150"
            :class="form.is_active ? 'bg-accent' : 'bg-white/[0.10]'"
          >
            <span
              class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-150"
              :class="form.is_active ? 'left-[18px]' : 'left-0.5'"
            />
          </button>
        </div>

        <!-- error -->
        <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
      </div>

      <div class="h-px bg-white/[0.06] mx-6" />

      <!-- footer -->
      <div class="flex justify-end gap-2 px-6 py-4">
        <button
          @click="$emit('update:open', false)"
          :disabled="loading"
          class="h-9 px-4 rounded-md text-sm text-fg-muted border border-white/[0.08]
                 hover:bg-white/[0.04] transition-colors disabled:opacity-50"
        >
          Отмена
        </button>
        <button
          @click="$emit('submit')"
          :disabled="loading || !canSubmit"
          class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-colors disabled:opacity-50"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          {{ loading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>
