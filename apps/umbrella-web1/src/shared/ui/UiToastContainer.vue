<script setup>
import { X, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-vue-next'
import { useToast } from '@/shared/composables/useToast'

const { toasts, remove } = useToast()

const ICONS = {
  success: CheckCircle2,
  error:   AlertCircle,
  warning: AlertTriangle,
}

const STYLES = {
  success: 'border-emerald-800/50 bg-emerald-950/80 text-emerald-300',
  error:   'border-red-800/50    bg-red-950/80    text-red-300',
  warning: 'border-amber-800/50  bg-amber-950/80  text-amber-300',
}

const ICON_STYLES = {
  success: 'text-emerald-400',
  error:   'text-red-400',
  warning: 'text-amber-400',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-5 left-1/2 -translate-x-1/2 z-[200] flex flex-col items-center gap-2 pointer-events-none">
      <TransitionGroup
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2 scale-95"
        enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 -translate-y-1 scale-95"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-start gap-3 min-w-[280px] max-w-sm
                 rounded-xl border px-4 py-3 backdrop-blur-sm shadow-lg"
          :class="STYLES[toast.type]"
        >
          <component :is="ICONS[toast.type]" :size="16" class="mt-0.5 shrink-0" :class="ICON_STYLES[toast.type]" />
          <span class="flex-1 text-sm leading-snug text-fg">{{ toast.message }}</span>
          <button
            @click="remove(toast.id)"
            class="shrink-0 text-fg-subtle/40 hover:text-fg-subtle transition-colors mt-0.5"
          >
            <X :size="14" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
