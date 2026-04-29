<script setup>
import {
  SelectRoot, SelectTrigger, SelectValue, SelectPortal, SelectContent,
  SelectViewport, SelectItem, SelectItemText, SelectItemIndicator,
} from 'reka-ui'
import { ChevronDown, Check } from 'lucide-vue-next'
import { cn } from '@/shared/lib/utils'

// reka-ui treats empty string as "nothing selected" — use a sentinel internally
const EMPTY = '__empty__'

const props = defineProps({
  modelValue:  { type: String, default: undefined },
  options:     { type: Array,  required: true }, // [{ value: string, label: string }]
  placeholder: { type: String, default: '' },
  class: {
    type: [Boolean, null, String, Object, Array],
    required: false,
    skipCheck: true,
  },
})

const emit = defineEmits(['update:modelValue'])

function toInternal(v) { return v === '' ? EMPTY : (v ?? EMPTY) }
function toExternal(v) { return v === EMPTY ? '' : v }
</script>

<template>
  <SelectRoot
    :model-value="toInternal(modelValue)"
    @update:model-value="emit('update:modelValue', toExternal($event))"
  >
    <SelectTrigger
      :class="cn(
        'flex items-center justify-between gap-2 outline-none transition-colors',
        props.class,
      )"
    >
      <SelectValue :placeholder="placeholder" />
      <ChevronDown :size="11" class="shrink-0 opacity-50" />
    </SelectTrigger>

    <SelectPortal>
      <SelectContent
        position="popper"
        :side-offset="4"
        class="z-50 min-w-[var(--reka-select-trigger-width)] overflow-hidden rounded-lg
               border border-white/[0.08] bg-bg-overlay shadow-xl
               data-[state=open]:animate-in data-[state=closed]:animate-out
               data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0
               data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95"
      >
        <SelectViewport class="p-1">
          <SelectItem
            v-for="opt in options"
            :key="opt.value"
            :value="toInternal(opt.value)"
            :class="cn(
              'relative flex cursor-pointer select-none items-center gap-2 rounded-md',
              'px-2.5 py-1.5 text-xs text-fg-subtle outline-none',
              'data-[highlighted]:bg-white/[0.06] data-[highlighted]:text-fg',
              'data-[state=checked]:text-fg transition-colors',
            )"
          >
            <SelectItemText>{{ opt.label }}</SelectItemText>
            <SelectItemIndicator class="ml-auto">
              <Check :size="10" class="text-accent" />
            </SelectItemIndicator>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>
