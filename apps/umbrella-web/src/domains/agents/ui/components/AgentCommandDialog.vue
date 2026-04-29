<script setup>
import { X, Package, RefreshCw } from 'lucide-vue-next'
import { releasesApi } from '@/domains/releases/api'

const props = defineProps({
  open:         Boolean,
  commandTypes: Array,
  typeLabels:   Object,
  type:         String,
  payload:      String,
  loading:      Boolean,
  error:        String,
  agentOs:      { type: String, default: null }, // 'windows' | 'linux' | 'macos'
})
const emit = defineEmits(['update:open', 'update:type', 'update:payload', 'submit'])

// ── update_self: releases picker ──────────────────────────────────────────────
const releases        = ref([])
const releasesLoading = ref(false)
const selectedRelease = ref(null)

watch(() => [props.open, props.type], async ([open, type]) => {
  if (!open || type !== 'update_self') return
  selectedRelease.value = null
  emit('update:payload', '')
  releasesLoading.value = true
  try {
    releases.value = await releasesApi.list(props.agentOs ?? undefined)
  } catch { releases.value = [] }
  finally   { releasesLoading.value = false }
}, { immediate: false })

watch(() => props.type, (t) => {
  if (t !== 'update_self') {
    selectedRelease.value = null
    releases.value = []
    emit('update:payload', '')
  }
})

function selectRelease(r) {
  selectedRelease.value = r
  emit('update:payload', JSON.stringify({ release_id: r.id, version: r.version, checksum: r.checksum }))
}

const submitDisabled = computed(() =>
  props.loading || (props.type === 'update_self' && !selectedRelease.value)
)

const PLATFORM_LABELS = { windows: 'Windows', linux: 'Linux', macos: 'macOS' }
function fmtSize(bytes) {
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' МБ'
  return (bytes / 1024).toFixed(0) + ' КБ'
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent :show-close-button="false" class="max-w-[480px] p-0 border-white/[0.08] bg-bg-raised gap-0">

      <!-- header -->
      <div class="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06]">
        <div>
          <DialogTitle class="text-base font-medium text-fg">Отправить команду</DialogTitle>
          <DialogDescription class="text-sm text-fg-subtle mt-0.5">
            Команда будет поставлена в очередь агенту.
          </DialogDescription>
        </div>
        <button @click="$emit('update:open', false)"
                class="text-fg-subtle hover:text-fg transition-colors mt-0.5">
          <X :size="18" />
        </button>
      </div>

      <!-- body -->
      <div class="px-6 py-5 flex flex-col gap-4">

        <div v-if="error"
             class="text-xs text-red-400 bg-red-950/30 border border-red-900/30 rounded-lg px-3 py-2.5">
          {{ error }}
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">Тип команды</label>
          <div class="flex gap-1.5 flex-wrap">
            <button
              v-for="t in commandTypes" :key="t"
              @click="$emit('update:type', t)"
              class="h-8 px-3 rounded-md text-xs border transition-colors"
              :class="type === t
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'"
            >
              {{ typeLabels[t] ?? t }}
            </button>
          </div>
        </div>

        <!-- releases picker for update_self -->
        <template v-if="type === 'update_self'">
          <div class="flex flex-col gap-1.5">
            <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">
              Релиз <span class="text-red-400">*</span>
            </label>

            <!-- loading -->
            <div v-if="releasesLoading" class="flex items-center justify-center gap-2 py-6 text-fg-subtle/40 text-xs">
              <RefreshCw :size="12" class="animate-spin" />
              Загрузка релизов...
            </div>

            <!-- empty -->
            <div v-else-if="!releases.length"
                 class="flex flex-col items-center gap-2 py-6 text-center rounded-lg border border-dashed border-white/[0.08]">
              <Package :size="20" class="text-fg-subtle/30" />
              <p class="text-xs text-fg-subtle/40">Нет доступных релизов</p>
              <p class="text-[10px] text-fg-subtle/30">Загрузите бинарь через страницу «Релизы»</p>
            </div>

            <!-- list -->
            <div v-else class="flex flex-col gap-1 max-h-52 overflow-y-auto">
              <button
                v-for="r in releases" :key="r.id"
                @click="selectRelease(r)"
                class="flex items-center justify-between px-3 py-2 rounded-lg border text-left transition-all"
                :class="selectedRelease?.id === r.id
                  ? 'border-accent/50 bg-accent/10'
                  : 'border-white/[0.08] hover:border-white/20 hover:bg-white/[0.03]'"
              >
                <div class="flex flex-col gap-0.5 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-medium text-fg">v{{ r.version }}</span>
                    <span class="text-[10px] text-fg-subtle/50">{{ PLATFORM_LABELS[r.platform] ?? r.platform }}</span>
                    <span class="text-[10px] text-fg-subtle/40">{{ r.arch }}</span>
                  </div>
                  <span class="text-[10px] text-fg-subtle/40 font-mono truncate">{{ r.filename }}</span>
                </div>
                <span class="text-[10px] text-fg-subtle/40 shrink-0 ml-2">{{ fmtSize(r.file_size) }}</span>
              </button>
            </div>
          </div>
        </template>

        <!-- generic JSON payload for all other commands -->
        <div v-else class="flex flex-col gap-1.5">
          <label class="text-[11px] font-semibold uppercase tracking-widest text-fg-subtle">
            Payload <span class="normal-case font-normal">(JSON, необязательно)</span>
          </label>
          <textarea
            :value="payload"
            rows="3"
            placeholder='{"key": "value"}'
            @input="$emit('update:payload', $event.target.value)"
            class="w-full rounded-md border border-white/[0.08] bg-bg px-3 py-2 text-sm text-fg font-mono
                   placeholder:text-fg-subtle/40 focus:outline-none focus:border-accent/50
                   transition-colors resize-none"
          />
        </div>

      </div>

      <!-- footer -->
      <div class="flex justify-end gap-2 px-6 pb-6">
        <button @click="$emit('update:open', false)" :disabled="loading"
                class="h-9 px-4 rounded-md text-sm text-fg-muted border border-white/[0.08]
                       hover:bg-white/[0.04] transition-colors disabled:opacity-50">
          Отмена
        </button>
        <button @click="$emit('submit')" :disabled="submitDisabled"
                class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
                style="background: linear-gradient(135deg, #c4683a, #d4785a)">
          {{ loading ? 'Отправка...' : 'Отправить' }}
        </button>
      </div>

    </DialogContent>
  </Dialog>
</template>
