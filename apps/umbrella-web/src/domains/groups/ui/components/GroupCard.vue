<script setup>
import { Pencil, Trash2, Users } from 'lucide-vue-next'
import { fallbackColor, colorDotStyle } from '@/domains/groups/groups.utils'
import { usePermissions } from '@/shared/composables/usePermissions'

const props = defineProps({
  group: { type: Object, required: true },
})
defineEmits(['edit', 'delete', 'members'])

const { canWrite } = usePermissions()

const accentColor = computed(() => props.group.color || fallbackColor(props.group.name))

const agentSuffix = computed(() => {
  const n = props.group.agents_count ?? 0
  const mod10  = n % 10
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 19) return 'ов'
  if (mod10 === 1) return ''
  if (mod10 >= 2 && mod10 <= 4) return 'а'
  return 'ов'
})
</script>

<template>
  <div class="group relative flex flex-col bg-bg-raised border border-white/[0.06] rounded-xl
              overflow-hidden transition-all duration-150
              hover:border-white/[0.12] hover:bg-bg-overlay">

    <!-- colored top strip -->
    <div class="h-1 w-full" :style="{ backgroundColor: accentColor }" />

    <!-- body — кликабельная область для перехода -->
    <RouterLink :to="`/groups/${group.id}`"
      class="flex flex-col flex-1 px-4 pt-3 pb-10 gap-1.5"
    >
      <!-- name + dot -->
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full shrink-0" :style="colorDotStyle(accentColor)" />
        <p class="text-base text-fg font-medium leading-tight truncate">{{ group.name }}</p>
      </div>

      <!-- description -->
      <p class="text-sm text-fg-subtle/70 leading-snug line-clamp-2 min-h-[2.5rem]">
        {{ group.description || '—' }}
      </p>

      <!-- agent count -->
      <button
        @click.prevent.stop="$emit('members', group)"
        class="mt-1 inline-flex items-center gap-1.5 text-xs text-fg-subtle
               hover:text-fg transition-colors self-start"
      >
        <Users :size="12" />
        {{ group.agents_count ?? 0 }} агент{{ agentSuffix }}
      </button>
    </RouterLink>

    <!-- actions — вне RouterLink, slide up on hover -->
    <div v-if="canWrite"
         class="absolute bottom-0 inset-x-0 flex items-center justify-end gap-0.5 px-3 py-2
                border-t border-white/[0.06] bg-bg-raised
                translate-y-full group-hover:translate-y-0
                transition-transform duration-150">
      <button @click="$emit('members', group)" title="Агенты"
              class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors">
        <Users :size="13" />
      </button>
      <button @click="$emit('edit', group)" title="Редактировать"
              class="p-1.5 rounded text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors">
        <Pencil :size="13" />
      </button>
      <button @click="$emit('delete', group)" title="Удалить"
              class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30 transition-colors">
        <Trash2 :size="13" />
      </button>
    </div>
  </div>
</template>
