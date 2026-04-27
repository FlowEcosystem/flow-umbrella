<script setup>
import { Pencil, Trash2, Check } from 'lucide-vue-next'
import { STATUS_LABELS, STATUS_CLASSES, STATUS_DOT, OS_LABELS, formatLastSeen } from '@/domains/agents/agents.utils'
import { usePermissions } from '@/shared/composables/usePermissions'

defineProps({
  agent:       { type: Object,  required: true },
  selected:    { type: Boolean, default: false },
  anySelected: { type: Boolean, default: false },
})

defineEmits(['edit', 'delete', 'select'])

const { canWrite } = usePermissions()
</script>

<template>
  <div class="group relative flex flex-col bg-bg-raised border rounded-xl
              overflow-hidden transition-all duration-150"
       :class="selected
         ? 'border-accent/50 bg-accent/5'
         : 'border-white/[0.06] hover:border-white/[0.12] hover:bg-bg-overlay'">

    <!-- checkbox — outside RouterLink so click doesn't trigger navigation -->
    <div
      class="absolute top-[18px] left-4 z-20 transition-opacity duration-150"
      :class="anySelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'"
      @click.stop="$emit('select', agent.id)"
    >
      <div class="w-4 h-4 rounded border flex items-center justify-center transition-colors cursor-pointer"
           :class="selected
             ? 'bg-accent border-accent'
             : 'border-white/30 bg-bg hover:border-accent/60'">
        <Check v-if="selected" :size="10" class="text-white" :stroke-width="3" />
      </div>
    </div>

    <!-- navigable content area -->
    <RouterLink :to="`/agents/${agent.id}`" class="flex flex-col flex-1 min-h-0">

      <!-- top: status + OS -->
      <div class="flex items-center justify-between px-4 pt-4 pb-3">
        <span class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded border transition-all duration-150"
              :class="[STATUS_CLASSES[agent.status], anySelected ? 'ml-5' : 'group-hover:ml-5']">
          <span class="w-1.5 h-1.5 rounded-full" :class="STATUS_DOT[agent.status]" />
          {{ STATUS_LABELS[agent.status] }}
        </span>
        <span class="text-xs text-fg-subtle/60">{{ OS_LABELS[agent.os] }}</span>
      </div>

      <!-- hostname -->
      <div class="px-4 pb-3 flex-1">
        <p class="text-base text-fg font-mono leading-tight truncate">{{ agent.hostname ?? '—' }}</p>
        <p class="text-sm text-fg-subtle mt-1 font-mono">{{ agent.ip_address ?? '—' }}</p>
      </div>

      <!-- bottom meta -->
      <div class="px-4 pb-4 flex items-center justify-between">
        <span class="text-xs text-fg-subtle/60">{{ formatLastSeen(agent.last_seen_at) }}</span>
        <span class="text-xs text-fg-subtle/60 font-mono">{{ agent.agent_version ?? '—' }}</span>
      </div>

    </RouterLink>

    <!-- actions — slide up on hover, hidden during bulk select -->
    <div v-if="canWrite && !anySelected"
         class="absolute bottom-0 inset-x-0 flex items-center justify-end gap-0.5 px-3 py-2
                border-t border-white/[0.06] bg-bg-raised z-10
                translate-y-full group-hover:translate-y-0
                transition-transform duration-150">
      <Tooltip>
        <TooltipTrigger as-child>
          <button @click.stop="$emit('edit', agent)"
                  class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors">
            <Pencil :size="13" />
          </button>
        </TooltipTrigger>
        <TooltipContent>Редактировать</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger as-child>
          <button @click.stop="$emit('delete', agent)"
                  class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30 transition-colors">
            <Trash2 :size="13" />
          </button>
        </TooltipTrigger>
        <TooltipContent>Удалить агента</TooltipContent>
      </Tooltip>
    </div>

  </div>
</template>
