<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  page:       { type: Number, required: true },
  totalPages: { type: Number, required: true },
})

const emit = defineEmits(['go'])

const pages = computed(() => {
  const total = props.totalPages
  const cur   = props.page
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const result = []
  const delta = 1

  result.push(1)
  if (cur - delta > 2) result.push('...')

  for (let i = Math.max(2, cur - delta); i <= Math.min(total - 1, cur + delta); i++) {
    result.push(i)
  }

  if (cur + delta < total - 1) result.push('...')
  result.push(total)

  return result
})
</script>

<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 pt-5">
    <button
      @click="emit('go', page - 1)"
      :disabled="page === 1"
      class="w-8 h-8 flex items-center justify-center rounded-md border border-white/[0.06]
             text-fg-subtle hover:text-fg hover:border-white/20 transition-colors
             disabled:opacity-30 disabled:cursor-not-allowed"
    >
      <ChevronLeft :size="14" />
    </button>

    <template v-for="p in pages" :key="p + '-' + page">
      <span v-if="p === '...'" class="w-8 h-8 flex items-center justify-center text-xs text-fg-subtle/40">
        ···
      </span>
      <button
        v-else
        @click="emit('go', p)"
        class="w-8 h-8 flex items-center justify-center rounded-md text-xs transition-colors"
        :class="p === page
          ? 'bg-accent/20 border border-accent/40 text-accent'
          : 'border border-transparent text-fg-subtle hover:text-fg hover:border-white/20'"
      >
        {{ p }}
      </button>
    </template>

    <button
      @click="emit('go', page + 1)"
      :disabled="page === totalPages"
      class="w-8 h-8 flex items-center justify-center rounded-md border border-white/[0.06]
             text-fg-subtle hover:text-fg hover:border-white/20 transition-colors
             disabled:opacity-30 disabled:cursor-not-allowed"
    >
      <ChevronRight :size="14" />
    </button>
  </div>
</template>
