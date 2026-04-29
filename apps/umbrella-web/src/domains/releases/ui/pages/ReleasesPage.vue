<script setup>
import { Trash2, RefreshCw, Package } from 'lucide-vue-next'
import { releasesApi } from '@/domains/releases/api'
import { useToast } from '@/shared/composables/useToast'
import { usePermissions } from '@/shared/composables/usePermissions'

const toast = useToast()
const { canWrite } = usePermissions()

// ── list ──────────────────────────────────────────────────────────────────────
const releases       = ref([])
const loading        = ref(false)
const filterPlatform = ref('')

async function fetchReleases() {
  loading.value = true
  try {
    releases.value = await releasesApi.list(filterPlatform.value || undefined)
  } catch (err) {
    toast.error(err.message ?? 'Ошибка загрузки релизов')
  } finally {
    loading.value = false
  }
}

onMounted(fetchReleases)
watch(filterPlatform, fetchReleases)

// ── delete ────────────────────────────────────────────────────────────────────
const deletingId = ref(null)

async function confirmDelete(id) {
  if (deletingId.value === id) {
    try {
      await releasesApi.remove(id)
      releases.value = releases.value.filter(r => r.id !== id)
      toast.success('Релиз удалён')
    } catch (err) {
      toast.error(err.message ?? 'Ошибка')
    } finally {
      deletingId.value = null
    }
  } else {
    deletingId.value = id
    setTimeout(() => { if (deletingId.value === id) deletingId.value = null }, 3000)
  }
}

// ── helpers ───────────────────────────────────────────────────────────────────
function fmtSize(bytes) {
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' МБ'
  return (bytes / 1024).toFixed(0) + ' КБ'
}

function fmtDate(dt) {
  return new Date(dt).toLocaleString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const PLATFORM_LABELS = { windows: 'Windows', linux: 'Linux', macos: 'macOS' }
const PLATFORM_COLORS = { windows: 'text-sky-400', linux: 'text-violet-400', macos: 'text-rose-400' }
const ARCH_COLORS     = { amd64: 'text-fg-subtle/60', arm64: 'text-amber-400/70' }
</script>

<template>
<div class="p-6 max-w-5xl mx-auto space-y-6">

  <!-- header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-lg font-semibold text-fg">Релизы агентов</h1>
      <p class="text-sm text-fg-subtle mt-0.5">Бинарные файлы для обновления агентов через команду</p>
    </div>
    <button @click="fetchReleases" :disabled="loading"
            class="h-8 px-3 rounded-md text-xs text-fg-subtle border border-white/[0.08]
                   hover:bg-white/[0.04] transition-colors disabled:opacity-50 flex items-center gap-1.5">
      <RefreshCw :size="12" :class="loading ? 'animate-spin' : ''" />
      Обновить
    </button>
  </div>

  <!-- platform filter -->
  <div class="flex gap-1.5">
    <button v-for="p in [['', 'Все'], ['linux', 'Linux'], ['windows', 'Windows'], ['macos', 'macOS']]"
            :key="p[0]"
            @click="filterPlatform = p[0]"
            class="h-7 px-3 rounded-md text-xs border transition-colors"
            :class="filterPlatform === p[0]
              ? 'border-accent/50 bg-accent/10 text-accent'
              : 'border-white/[0.08] text-fg-subtle hover:text-fg hover:border-white/20'">
      {{ p[1] }}
    </button>
  </div>

  <!-- table -->
  <div class="rounded-xl border border-white/[0.07] overflow-hidden">

    <!-- skeleton -->
    <template v-if="loading && !releases.length">
      <div v-for="i in 3" :key="i" class="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-4 py-3 border-b border-white/[0.04] animate-pulse">
        <div class="w-16 h-3.5 bg-white/[0.06] rounded" />
        <div class="h-3.5 bg-white/[0.06] rounded" />
        <div class="w-12 h-3.5 bg-white/[0.06] rounded" />
        <div class="w-24 h-3.5 bg-white/[0.06] rounded" />
        <div class="w-8 h-3.5 bg-white/[0.06] rounded" />
      </div>
    </template>

    <!-- empty -->
    <div v-else-if="!releases.length"
         class="flex flex-col items-center justify-center gap-3 py-14 text-center">
      <Package :size="32" class="text-fg-subtle/30" />
      <p class="text-sm text-fg-subtle/50">Нет доступных релизов</p>
      <p class="text-xs text-fg-subtle/30">Положите бинарь в директорию релизов на сервере</p>
    </div>

    <!-- rows -->
    <template v-else>
      <div class="grid grid-cols-[80px_1fr_80px_100px_160px_80px] gap-3 px-4 py-2
                  border-b border-white/[0.06] text-[11px] font-semibold uppercase
                  tracking-widest text-fg-subtle/40">
        <span>Версия</span>
        <span>Файл</span>
        <span>Арх.</span>
        <span>Размер</span>
        <span>Изменён</span>
        <span v-if="canWrite" class="text-right">Действия</span>
      </div>

      <div v-for="r in releases" :key="r.id"
           class="grid grid-cols-[80px_1fr_80px_100px_160px_80px] gap-3 px-4 py-2.5
                  items-center border-b border-white/[0.04] last:border-0
                  hover:bg-white/[0.015] transition-colors">

        <div class="flex flex-col gap-0.5">
          <span class="text-xs font-mono font-medium text-fg">{{ r.version }}</span>
          <span class="text-[10px]" :class="PLATFORM_COLORS[r.platform] ?? 'text-fg-subtle'">
            {{ PLATFORM_LABELS[r.platform] ?? r.platform }}
          </span>
        </div>

        <span class="text-xs font-mono text-fg-subtle/70 truncate" :title="r.filename">{{ r.filename }}</span>

        <span class="text-xs" :class="ARCH_COLORS[r.arch] ?? 'text-fg-subtle'">{{ r.arch }}</span>

        <span class="text-xs text-fg-subtle/60">{{ fmtSize(r.file_size) }}</span>

        <span class="text-xs text-fg-subtle/50">{{ fmtDate(r.uploaded_at) }}</span>

        <div v-if="canWrite" class="flex justify-end">
          <Tooltip>
            <TooltipTrigger as-child>
              <button @click="confirmDelete(r.id)"
                      class="h-6 w-6 rounded flex items-center justify-center transition-all"
                      :class="deletingId === r.id
                        ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                        : 'text-fg-subtle/40 hover:text-red-400 hover:bg-red-950/30'">
                <Trash2 :size="12" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              {{ deletingId === r.id ? 'Ещё раз — релиз будет удалён' : 'Удалить релиз' }}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </template>
  </div>

</div>
</template>
