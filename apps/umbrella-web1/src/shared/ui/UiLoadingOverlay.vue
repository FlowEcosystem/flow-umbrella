<script setup>
import { RefreshCw } from 'lucide-vue-next'

defineProps({
  loading:  { type: Boolean, default: false },
  label:    { type: String,  default: 'Загрузка...' },
})
</script>

<template>
  <div class="relative">
    <slot />
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-150"
      leave-to-class="opacity-0"
    >
      <div
        v-if="loading"
        class="absolute inset-0 z-10 flex items-center justify-center rounded-[inherit]
               bg-bg/60 backdrop-blur-[1px]"
      >
        <div class="flex items-center gap-2 text-sm text-fg-subtle">
          <RefreshCw :size="14" class="animate-spin" />
          {{ label }}
        </div>
      </div>
    </Transition>
  </div>
</template>
