<script setup>
import { X, Users, CheckSquare, ChevronDown, Loader2 } from 'lucide-vue-next'
import { useGroupsStore } from '@/domains/groups/store'

const props = defineProps({
  selectedCount:    { type: Number,   required: true },
  totalCount:       { type: Number,   required: true },
  allSelected:      { type: Boolean,  default: false },
  statusLoading:    { type: Boolean,  default: false },
  groupLoading:     { type: Boolean,  default: false },
})

defineEmits(['clear', 'select-all', 'set-status', 'add-to-group'])

const groupsStore = useGroupsStore()
const groupDropOpen = ref(false)
const groupDropRef = ref(null)

function onDocClick(e) {
  if (groupDropRef.value && !groupDropRef.value.contains(e.target)) {
    groupDropOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  if (!groupsStore.items.length) groupsStore.fetch()
})
onUnmounted(() => document.removeEventListener('click', onDocClick))

const STATUS_OPTIONS = [
  { value: 'active',         label: 'Активен',  dot: 'bg-emerald-400' },
  { value: 'disabled',       label: 'Отключён', dot: 'bg-fg-subtle' },
  { value: 'decommissioned', label: 'Выведен',  dot: 'bg-red-400' },
]
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-4"
      leave-active-class="transition-all duration-150 ease-in"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div v-if="selectedCount > 0"
           class="fixed bottom-10 left-1/2 -translate-x-1/2 z-[150]
                  flex items-center gap-2 px-3 py-2 rounded-xl
                  bg-bg-overlay border border-white/[0.12] shadow-xl shadow-black/40
                  backdrop-blur-sm">

        <!-- count + select all -->
        <div class="flex items-center gap-2 pr-2 border-r border-white/[0.1]">
          <span class="text-sm text-fg font-medium tabular-nums">{{ selectedCount }}</span>
          <span class="text-xs text-fg-subtle">
            агент{{ selectedCount === 1 ? '' : selectedCount >= 2 && selectedCount <= 4 ? 'а' : 'ов' }}
          </span>
          <button
            @click="$emit('select-all')"
            class="flex items-center gap-1 text-xs px-2 py-1 rounded-md transition-colors"
            :class="allSelected
              ? 'text-accent bg-accent/10'
              : 'text-fg-subtle hover:text-fg hover:bg-white/[0.06]'"
            title="Выбрать все на странице"
          >
            <CheckSquare :size="12" />
            {{ allSelected ? 'Все' : 'Выбрать все' }}
          </button>
        </div>

        <!-- set status -->
        <div class="flex items-center gap-1">
          <span class="text-xs text-fg-subtle/60 mr-0.5">Статус:</span>
          <button
            v-for="s in STATUS_OPTIONS"
            :key="s.value"
            @click="$emit('set-status', s.value)"
            :disabled="statusLoading"
            class="flex items-center gap-1.5 h-7 px-2.5 rounded-md text-xs border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
          >
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="s.dot" />
            {{ s.label }}
          </button>
          <Loader2 v-if="statusLoading" :size="13" class="animate-spin text-fg-subtle ml-1" />
        </div>

        <!-- divider -->
        <div class="w-px h-5 bg-white/[0.1]" />

        <!-- add to group -->
        <div class="relative" ref="groupDropRef">
          <button
            @click="groupDropOpen = !groupDropOpen"
            :disabled="groupLoading"
            class="flex items-center gap-1.5 h-7 px-2.5 rounded-md text-xs border border-white/[0.08]
                   text-fg-subtle hover:text-fg hover:border-white/20 transition-colors disabled:opacity-40"
          >
            <Users :size="12" />
            В группу
            <Loader2 v-if="groupLoading" :size="11" class="animate-spin" />
            <ChevronDown v-else :size="11" :class="groupDropOpen ? 'rotate-180' : ''" class="transition-transform" />
          </button>

          <Transition
            enter-active-class="transition-all duration-150 ease-out"
            enter-from-class="opacity-0 -translate-y-1 scale-[0.97]"
            leave-active-class="transition-all duration-100 ease-in"
            leave-to-class="opacity-0 -translate-y-1 scale-[0.97]"
          >
            <div v-if="groupDropOpen"
                 class="absolute bottom-full mb-1.5 left-0 min-w-[180px] max-h-48 overflow-y-auto
                        rounded-lg border border-white/[0.1] bg-bg-overlay shadow-xl shadow-black/40
                        py-1 z-[160]">
              <div v-if="groupsStore.isLoading" class="px-3 py-2 text-xs text-fg-subtle/50">
                Загрузка...
              </div>
              <div v-else-if="!groupsStore.items.length" class="px-3 py-2 text-xs text-fg-subtle/50">
                Групп нет
              </div>
              <button
                v-else
                v-for="group in groupsStore.items"
                :key="group.id"
                @click="$emit('add-to-group', group.id); groupDropOpen = false"
                class="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-fg-subtle
                       hover:text-fg hover:bg-white/[0.05] transition-colors text-left"
              >
                <span class="w-1.5 h-1.5 rounded-full shrink-0 bg-accent/60" />
                {{ group.name }}
              </button>
            </div>
          </Transition>
        </div>

        <!-- divider -->
        <div class="w-px h-5 bg-white/[0.1]" />

        <!-- clear -->
        <button
          @click="$emit('clear')"
          class="p-1.5 rounded-md text-fg-subtle hover:text-fg hover:bg-white/[0.06] transition-colors"
          title="Снять выделение"
        >
          <X :size="14" />
        </button>

      </div>
    </Transition>
  </Teleport>
</template>
