<script setup>
import { X, UserMinus, UserPlus, Search, Users, RefreshCw } from 'lucide-vue-next'
import { OS_LABELS, STATUS_DOT } from '@/domains/agents/agents.utils'
import { usePermissions } from '@/shared/composables/usePermissions'

const props = defineProps({
  open:            { type: Boolean,  required: true },
  group:           { type: Object,   default: null },
  members:         { type: Array,    default: () => [] },
  available:       { type: Array,    default: () => [] },
  loading:         { type: Boolean,  default: false },
  error:           { type: String,   default: '' },
  addLoading:      { type: Boolean,  default: false },
  removeLoading:   { type: Object,   default: () => ({}) },
})

defineEmits(['update:open', 'add', 'remove'])

const tab    = ref('members')
const search = ref('')

const filteredMembers = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.members
  return props.members.filter(a =>
    a.hostname.toLowerCase().includes(q) || (a.ip_address ?? '').includes(q)
  )
})

const filteredAvailable = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.available
  return props.available.filter(a =>
    a.hostname.toLowerCase().includes(q) || (a.ip_address ?? '').includes(q)
  )
})

watch(() => props.open, v => { if (v) { tab.value = 'members'; search.value = '' } })

const { canWrite } = usePermissions()
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent
      :show-close-button="false"
      class="max-w-[520px] p-0 border-white/[0.08] bg-bg-raised gap-0 flex flex-col max-h-[80vh]"
    >
      <!-- header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">Агенты группы</DialogTitle>
          <DialogDescription class="text-xs text-fg-subtle mt-0.5">{{ group?.name ?? '' }}</DialogDescription>
        </div>
        <button
          @click="$emit('update:open', false)"
          class="text-fg-subtle hover:text-fg transition-colors"
        >
          <X :size="16" />
        </button>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <!-- tabs -->
      <div class="flex gap-1 px-6 pt-3 pb-2 shrink-0">
        <button
          v-for="t in canWrite
            ? [{ id: 'members', label: 'В группе' }, { id: 'add', label: 'Добавить' }]
            : [{ id: 'members', label: 'В группе' }]"
          :key="t.id"
          @click="tab = t.id; search = ''"
          class="h-7 px-3 rounded-md text-xs border transition-all duration-150"
          :class="tab === t.id
            ? 'border-accent/50 bg-accent/10 text-accent'
            : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
        >
          {{ t.label }}
          <span v-if="t.id === 'members'" class="ml-1 opacity-60">{{ members.length }}</span>
          <span v-if="t.id === 'add'" class="ml-1 opacity-60">{{ available.length }}</span>
        </button>
      </div>

      <!-- search -->
      <div class="px-6 pb-3 shrink-0">
        <div class="relative">
          <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-subtle/50 pointer-events-none" />
          <input
            v-model="search"
            placeholder="Поиск по hostname / IP..."
            class="h-8 w-full rounded-md border border-white/[0.08] bg-bg pl-8 pr-3 text-xs text-fg
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
          />
        </div>
      </div>

      <!-- list -->
      <div class="flex-1 overflow-y-auto px-6 pb-4 min-h-0">

        <!-- loading -->
        <div v-if="loading" class="flex items-center justify-center py-10">
          <RefreshCw :size="16" class="text-fg-subtle/50 animate-spin" />
        </div>

        <!-- error -->
        <p v-else-if="error" class="text-xs text-red-400 py-4 text-center">{{ error }}</p>

        <!-- members tab -->
        <template v-else-if="tab === 'members'">
          <div v-if="!filteredMembers.length"
               class="flex flex-col items-center gap-2 py-10 text-center">
            <Users :size="22" :stroke-width="1.3" class="text-fg-subtle/40" />
            <p class="text-xs text-fg-subtle">
              {{ members.length ? 'Ничего не найдено' : 'В группе пока нет агентов' }}
            </p>
          </div>
          <div v-else class="flex flex-col gap-1">
            <div
              v-for="agent in filteredMembers"
              :key="agent.id"
              class="flex items-center justify-between px-3 py-2.5 rounded-lg
                     bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.08]
                     transition-colors"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="STATUS_DOT[agent.status]" />
                <span class="text-sm text-fg font-mono truncate">{{ agent.hostname }}</span>
                <span class="text-xs text-fg-subtle/60 font-mono shrink-0">{{ agent.ip_address ?? '' }}</span>
              </div>
              <button
                v-if="canWrite"
                @click="$emit('remove', agent.id)"
                :disabled="removeLoading[agent.id]"
                class="p-1.5 rounded text-fg-subtle hover:text-red-400 hover:bg-red-950/30
                       transition-colors disabled:opacity-40 shrink-0 ml-2"
                title="Убрать из группы"
              >
                <UserMinus :size="13" />
              </button>
            </div>
          </div>
        </template>

        <!-- add tab -->
        <template v-else>
          <div v-if="!filteredAvailable.length"
               class="flex flex-col items-center gap-2 py-10 text-center">
            <Users :size="22" :stroke-width="1.3" class="text-fg-subtle/40" />
            <p class="text-xs text-fg-subtle">
              {{ available.length ? 'Ничего не найдено' : 'Все агенты уже в группе' }}
            </p>
          </div>
          <div v-else class="flex flex-col gap-1">
            <div
              v-for="agent in filteredAvailable"
              :key="agent.id"
              class="flex items-center justify-between px-3 py-2.5 rounded-lg
                     bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.08]
                     transition-colors"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="STATUS_DOT[agent.status]" />
                <span class="text-sm text-fg font-mono truncate">{{ agent.hostname }}</span>
                <span class="text-xs text-fg-subtle/60 font-mono shrink-0">{{ agent.ip_address ?? '' }}</span>
              </div>
              <button
                @click="$emit('add', agent.id)"
                :disabled="addLoading"
                class="p-1.5 rounded text-fg-subtle hover:text-accent hover:bg-accent/10
                       transition-colors disabled:opacity-40 shrink-0 ml-2"
                title="Добавить в группу"
              >
                <UserPlus :size="13" />
              </button>
            </div>
          </div>
        </template>
      </div>
    </DialogContent>
  </Dialog>
</template>
