<script setup>
import { X } from 'lucide-vue-next'
import { COLOR_PRESETS } from '@/domains/groups/groups.utils'

const props = defineProps({
  open:    { type: Boolean, required: true },
  form:    { type: Object,  required: true },
  target:  { type: Object,  default: null },
  loading: { type: Boolean, default: false },
  error:   { type: String,  default: '' },
})

const emit = defineEmits(['update:open', 'submit'])

const isEdit = computed(() => !!props.target)
const title  = computed(() => isEdit.value ? 'Редактировать группу' : 'Новая группа')
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
        <button
          @click="$emit('update:open', false)"
          :disabled="loading"
          class="text-fg-subtle hover:text-fg transition-colors disabled:opacity-40"
        >
          <X :size="16" />
        </button>
      </div>

      <div class="h-px bg-white/[0.06] mx-6" />

      <!-- body -->
      <div class="px-6 py-5 flex flex-col gap-4">

        <!-- name -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Название</label>
          <input
            v-model="form.name"
            placeholder="prod-servers"
            class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>

        <!-- description -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-fg-subtle">Описание <span class="opacity-40">(необязательно)</span></label>
          <textarea
            v-model="form.description"
            placeholder="Краткое описание группы..."
            rows="2"
            class="rounded-md border border-white/[0.08] bg-bg px-3 py-2 text-sm text-fg resize-none
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>

        <!-- color -->
        <div class="flex flex-col gap-2">
          <label class="text-xs text-fg-subtle">Цвет</label>
          <div class="flex items-center gap-2 flex-wrap">
            <button
              v-for="c in COLOR_PRESETS"
              :key="c"
              type="button"
              @click="form.color = c"
              class="w-6 h-6 rounded-full border-2 transition-all duration-100 shrink-0"
              :style="{ backgroundColor: c }"
              :class="form.color === c
                ? 'border-white/70 scale-110'
                : 'border-transparent hover:border-white/30'"
            />
            <!-- none -->
            <button
              type="button"
              @click="form.color = ''"
              class="w-6 h-6 rounded-full border-2 transition-all duration-100 shrink-0
                     bg-white/[0.06]"
              :class="!form.color
                ? 'border-white/50'
                : 'border-transparent hover:border-white/30'"
              title="Без цвета"
            />
          </div>
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
          :disabled="loading || !form.name.trim()"
          class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-colors disabled:opacity-50"
          style="background: linear-gradient(135deg, #c4683a, #d4785a)"
        >
          {{ loading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>
