<script setup>
import { Globe, Users, Monitor, Search, X, Loader2, Check } from 'lucide-vue-next'
import { policiesApi } from '@/domains/policies/api'
import { groupsApi }   from '@/domains/groups/api'
import { agentsApi }   from '@/domains/agents/api'

const props = defineProps({
  open:       { type: Boolean, required: true },
  policyId:   { type: String,  default: null },
  policyName: { type: String,  default: '' },
})
const emit = defineEmits(['update:open', 'saved'])

// ── state ──────────────────────────────────────────────────────
const loading     = ref(false)
const saveLoading = ref(false)
const error       = ref('')

const isGlobal       = ref(false)
const selectedGroups = ref(new Set())
const selectedAgents = ref(new Set())

const allGroups = ref([])
const allAgents = ref([])
const groupSearch = ref('')
const agentSearch = ref('')

// ── computed lists ─────────────────────────────────────────────
const filteredGroups = computed(() => {
  const q = groupSearch.value.trim().toLowerCase()
  return q ? allGroups.value.filter(g => g.name.toLowerCase().includes(q)) : allGroups.value
})

const filteredAgents = computed(() => {
  const q = agentSearch.value.trim().toLowerCase()
  return q
    ? allAgents.value.filter(a => a.hostname.toLowerCase().includes(q))
    : allAgents.value
})

// ── load on open ───────────────────────────────────────────────
watch(() => props.open, async (v) => {
  if (!v || !props.policyId) return
  loading.value     = true
  error.value       = ''
  groupSearch.value = ''
  agentSearch.value = ''
  try {
    const [assignments, groupsData, agentsData] = await Promise.all([
      policiesApi.getAssignments(props.policyId),
      groupsApi.list({ limit: 200 }),
      agentsApi.list({ limit: 200, status: 'active' }),
    ])
    isGlobal.value       = assignments.is_global
    selectedGroups.value = new Set(assignments.groups.map(g => g.group_id))
    selectedAgents.value = new Set(assignments.agents.map(a => a.agent_id))
    allGroups.value      = groupsData.items ?? []
    allAgents.value      = agentsData.items ?? []
  } catch (e) {
    error.value = e.message ?? 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
})

// ── toggle helpers ─────────────────────────────────────────────
function toggleGroup(id) {
  const next = new Set(selectedGroups.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedGroups.value = next
}

function toggleAgent(id) {
  const next = new Set(selectedAgents.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedAgents.value = next
}

// ── save ───────────────────────────────────────────────────────
async function save() {
  saveLoading.value = true
  error.value       = ''
  try {
    await policiesApi.assign(props.policyId, {
      is_global:  isGlobal.value,
      group_ids:  [...selectedGroups.value],
      agent_ids:  [...selectedAgents.value],
    })
    emit('saved')
    emit('update:open', false)
  } catch (e) {
    error.value = e.message ?? 'Ошибка сохранения'
  } finally {
    saveLoading.value = false
  }
}

function close() { emit('update:open', false) }

const summaryText = computed(() => {
  if (isGlobal.value) return 'Все агенты'
  const parts = []
  if (selectedGroups.value.size) parts.push(`${selectedGroups.value.size} гр.`)
  if (selectedAgents.value.size) parts.push(`${selectedAgents.value.size} аг.`)
  return parts.length ? parts.join(', ') : 'Не назначена'
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-100"
      leave-to-class="opacity-0"
    >
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="close" />

        <div class="relative z-10 w-full max-w-2xl bg-bg-raised border border-white/[0.10] rounded-2xl
                    shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">

          <!-- header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
            <div>
              <h2 class="text-base text-fg font-medium">Назначить политику</h2>
              <p class="text-xs text-fg-subtle/60 mt-0.5 truncate max-w-sm">{{ policyName }}</p>
            </div>
            <button @click="close"
                    class="p-1.5 rounded-md text-fg-subtle/50 hover:text-fg hover:bg-white/[0.06] transition-colors">
              <X :size="15" />
            </button>
          </div>

          <!-- loading skeleton -->
          <div v-if="loading" class="flex-1 flex items-center justify-center py-16">
            <Loader2 :size="20" class="animate-spin text-fg-subtle/40" />
          </div>

          <!-- error -->
          <div v-else-if="error && !allGroups.length" class="flex-1 flex items-center justify-center py-16">
            <p class="text-sm text-red-400">{{ error }}</p>
          </div>

          <!-- content -->
          <div v-else class="flex-1 overflow-y-auto">

            <!-- global toggle -->
            <div class="px-6 py-4 border-b border-white/[0.05]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <Globe :size="15" class="text-blue-400/70 shrink-0" />
                  <div>
                    <p class="text-sm text-fg font-medium">Глобально</p>
                    <p class="text-xs text-fg-subtle/60">Применить ко всем активным агентам</p>
                  </div>
                </div>
                <button
                  @click="isGlobal = !isGlobal"
                  class="relative w-10 h-[22px] rounded-full border transition-all duration-200 shrink-0"
                  :class="isGlobal
                    ? 'bg-blue-500/20 border-blue-500/50'
                    : 'bg-white/[0.04] border-white/[0.12]'"
                >
                  <span
                    class="absolute top-[3px] w-[15px] h-[15px] rounded-full transition-all duration-200"
                    :class="isGlobal ? 'left-[22px] bg-blue-400' : 'left-[3px] bg-fg-subtle/40'"
                  />
                </button>
              </div>

              <!-- summary badge -->
              <div class="mt-3 flex items-center gap-2">
                <span class="text-xs text-fg-subtle/50">Итого:</span>
                <span class="text-xs px-2 py-0.5 rounded border"
                      :class="isGlobal
                        ? 'border-blue-800/40 bg-blue-950/30 text-blue-400'
                        : (selectedGroups.size || selectedAgents.size)
                          ? 'border-accent/30 bg-accent/10 text-accent'
                          : 'border-white/[0.08] text-fg-subtle/50'">
                  {{ summaryText }}
                </span>
              </div>
            </div>

            <!-- two-column: groups + agents -->
            <div class="grid grid-cols-2 divide-x divide-white/[0.05]"
                 :class="isGlobal ? 'opacity-40 pointer-events-none' : ''">

              <!-- groups -->
              <div class="flex flex-col">
                <div class="px-4 pt-4 pb-2">
                  <div class="flex items-center gap-2 mb-2.5">
                    <Users :size="13" class="text-fg-subtle/60" />
                    <span class="text-xs text-fg-subtle uppercase tracking-wider">
                      Группы
                    </span>
                    <span v-if="selectedGroups.size"
                          class="text-xs px-1.5 py-0.5 rounded bg-accent/15 text-accent tabular-nums">
                      {{ selectedGroups.size }}
                    </span>
                  </div>
                  <div class="relative">
                    <Search :size="11" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
                    <input
                      v-model="groupSearch"
                      placeholder="Поиск..."
                      class="h-7 w-full rounded-md border border-white/[0.07] bg-bg pl-7 pr-3 text-xs text-fg
                             placeholder:text-fg-subtle/35 focus:outline-none focus:border-white/15 transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto max-h-52 divide-y divide-white/[0.03] px-2 pb-2">
                  <div v-if="!filteredGroups.length" class="py-4 text-center text-xs text-fg-subtle/40">
                    {{ groupSearch ? 'Не найдено' : 'Нет групп' }}
                  </div>
                  <button
                    v-for="g in filteredGroups"
                    :key="g.id"
                    @click="toggleGroup(g.id)"
                    class="w-full flex items-center gap-2 px-2 py-2 rounded-md text-left transition-colors
                           hover:bg-white/[0.03]"
                    :class="selectedGroups.has(g.id) ? 'bg-accent/[0.07]' : ''"
                  >
                    <span class="w-3.5 h-3.5 rounded flex items-center justify-center border shrink-0 transition-all"
                          :class="selectedGroups.has(g.id)
                            ? 'border-accent bg-accent/20 text-accent'
                            : 'border-white/[0.15] text-transparent'">
                      <Check :size="9" />
                    </span>
                    <span class="w-1.5 h-1.5 rounded-full shrink-0"
                          :style="{ backgroundColor: g.color || '#8b8b8b' }" />
                    <span class="text-xs text-fg flex-1 truncate">{{ g.name }}</span>
                  </button>
                </div>
              </div>

              <!-- agents -->
              <div class="flex flex-col">
                <div class="px-4 pt-4 pb-2">
                  <div class="flex items-center gap-2 mb-2.5">
                    <Monitor :size="13" class="text-fg-subtle/60" />
                    <span class="text-xs text-fg-subtle uppercase tracking-wider">
                      Агенты
                    </span>
                    <span v-if="selectedAgents.size"
                          class="text-xs px-1.5 py-0.5 rounded bg-accent/15 text-accent tabular-nums">
                      {{ selectedAgents.size }}
                    </span>
                  </div>
                  <div class="relative">
                    <Search :size="11" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-fg-subtle/40 pointer-events-none" />
                    <input
                      v-model="agentSearch"
                      placeholder="Поиск..."
                      class="h-7 w-full rounded-md border border-white/[0.07] bg-bg pl-7 pr-3 text-xs text-fg
                             placeholder:text-fg-subtle/35 focus:outline-none focus:border-white/15 transition-colors"
                    />
                  </div>
                </div>

                <div class="overflow-y-auto max-h-52 divide-y divide-white/[0.03] px-2 pb-2">
                  <div v-if="!filteredAgents.length" class="py-4 text-center text-xs text-fg-subtle/40">
                    {{ agentSearch ? 'Не найдено' : 'Нет активных агентов' }}
                  </div>
                  <button
                    v-for="a in filteredAgents"
                    :key="a.id"
                    @click="toggleAgent(a.id)"
                    class="w-full flex items-center gap-2 px-2 py-2 rounded-md text-left transition-colors
                           hover:bg-white/[0.03]"
                    :class="selectedAgents.has(a.id) ? 'bg-accent/[0.07]' : ''"
                  >
                    <span class="w-3.5 h-3.5 rounded flex items-center justify-center border shrink-0 transition-all"
                          :class="selectedAgents.has(a.id)
                            ? 'border-accent bg-accent/20 text-accent'
                            : 'border-white/[0.15] text-transparent'">
                      <Check :size="9" />
                    </span>
                    <span class="text-xs font-mono text-fg flex-1 truncate">{{ a.hostname }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- footer -->
          <div class="flex items-center justify-between px-6 py-4 border-t border-white/[0.06] bg-bg/30">
            <p v-if="error" class="text-xs text-red-400">{{ error }}</p>
            <div v-else />
            <div class="flex items-center gap-2">
              <button @click="close"
                      class="h-8 px-4 rounded-lg text-xs border border-white/[0.08] text-fg-subtle
                             hover:text-fg hover:border-white/20 transition-colors">
                Отмена
              </button>
              <button
                @click="save"
                :disabled="saveLoading || loading"
                class="h-8 px-4 rounded-lg text-xs font-medium text-[#1c1917] disabled:opacity-50 transition-opacity"
                style="background: linear-gradient(135deg, #c4683a, #d4785a)"
              >
                <Loader2 v-if="saveLoading" :size="13" class="animate-spin inline mr-1" />
                Сохранить
              </button>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>
