<script setup>
import { Upload, X, CheckCircle2, AlertCircle, Info, FileText } from 'lucide-vue-next'
import { useServicesStore } from '@/domains/policies/servicesStore'
import { useToast }         from '@/shared/composables/useToast'

const props = defineProps({
  open: { type: Boolean, required: true },
})
const emit = defineEmits(['update:open'])

const store = useServicesStore()
const toast = useToast()

const step     = ref('pick')   // 'pick' | 'preview'
const dragOver = ref(false)
const fileInput = ref(null)

const toCreate = ref([])  // { name, category, rules[] }
const skipped  = ref([])  // { name, category, reason }
const invalid  = ref([])  // { row, reason }

const importing   = ref(false)
const importError = ref('')

function reset() {
  step.value = 'pick'
  toCreate.value = []
  skipped.value  = []
  invalid.value  = []
  importing.value   = false
  importError.value = ''
  dragOver.value    = false
  if (fileInput.value) fileInput.value.value = ''
}

watch(() => props.open, v => { if (!v) reset() })

// --- CSV parsing ---
const IP_RE      = /^(\d{1,3}\.){3}\d{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$/
const VALID_TYPES = new Set(['domain', 'url', 'ip'])

function parseCSV(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim())
  if (!lines.length) return

  const firstLower = lines[0].toLowerCase()
  const hasHeader  = firstLower.includes('name') || firstLower.includes('category')
  const dataLines  = hasHeader ? lines.slice(1) : lines

  const serviceMap = new Map()  // "name::category" -> svc
  const rowInvalid = []

  dataLines.forEach((line, idx) => {
    const rowNum = hasHeader ? idx + 2 : idx + 1
    const cols   = line.split(',').map(c => c.trim().replace(/^["']|["']$/g, ''))
    const [name, category, ruleType, ruleValue] = cols

    if (!name || !category) {
      rowInvalid.push({ row: rowNum, reason: !name ? 'Пустое название сервиса' : 'Пустая категория' })
      return
    }

    const key = `${name.toLowerCase()}::${category}`
    if (!serviceMap.has(key)) serviceMap.set(key, { name, category, rules: [] })

    if (ruleType || ruleValue) {
      if (!ruleType || !ruleValue) {
        rowInvalid.push({ row: rowNum, reason: 'Указан тип правила без значения или наоборот' })
        return
      }
      if (!VALID_TYPES.has(ruleType)) {
        rowInvalid.push({ row: rowNum, reason: `Неизвестный тип «${ruleType}» — допустимы: domain, url, ip` })
        return
      }
      if (ruleType === 'ip' && !IP_RE.test(ruleValue)) {
        rowInvalid.push({ row: rowNum, reason: `Неверный IP/CIDR: «${ruleValue}»` })
        return
      }
      if (ruleType === 'url') {
        try { new URL(ruleValue) } catch {
          rowInvalid.push({ row: rowNum, reason: `Неверный URL: «${ruleValue}»` })
          return
        }
      }
      serviceMap.get(key).rules.push({ type: ruleType, value: ruleValue })
    }
  })

  const existingNames = new Set(store.items.map(s => s.name.toLowerCase()))
  const newServices   = []
  const skippedSvcs   = []

  for (const svc of serviceMap.values()) {
    if (existingNames.has(svc.name.toLowerCase())) {
      skippedSvcs.push({ name: svc.name, category: svc.category, reason: 'Уже существует' })
    } else {
      newServices.push(svc)
    }
  }

  toCreate.value = newServices
  skipped.value  = skippedSvcs
  invalid.value  = rowInvalid
  step.value     = 'preview'
}

function handleFile(file) {
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) {
    toast.error('Поддерживаются только файлы .csv')
    return
  }
  const reader = new FileReader()
  reader.onload = e => parseCSV(e.target.result)
  reader.readAsText(file, 'utf-8')
}

function onDrop(e) {
  dragOver.value = false
  handleFile(e.dataTransfer.files[0])
}

// --- import ---
async function doImport() {
  importing.value   = true
  importError.value = ''
  try {
    await Promise.all(toCreate.value.map(svc => store.create(svc)))
    toast.success(`Добавлено сервисов: ${toCreate.value.length}`)
    emit('update:open', false)
  } catch (err) {
    importError.value = err.response?.data?.message ?? 'Ошибка при импорте'
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="v => !v && emit('update:open', false)">
    <DialogContent
      :show-close-button="false"
      class="max-w-[580px] p-0 border-white/[0.08] bg-bg-raised gap-0 flex flex-col max-h-[88vh]"
    >
      <!-- header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <div>
          <DialogTitle class="text-base font-medium text-fg">Импорт из CSV</DialogTitle>
          <DialogDescription class="text-xs text-fg-subtle mt-0.5">
            {{ step === 'pick'
              ? 'Загрузите файл CSV со списком сервисов'
              : `${toCreate.length} новых · ${skipped.length} пропущено · ${invalid.length} ошибок` }}
          </DialogDescription>
        </div>
        <button @click="emit('update:open', false)" class="text-fg-subtle hover:text-fg transition-colors">
          <X :size="16" />
        </button>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <!-- STEP: pick -->
      <div v-if="step === 'pick'" class="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-4">

        <!-- drop zone -->
        <div
          @dragover.prevent="dragOver = true"
          @dragleave="dragOver = false"
          @drop.prevent="onDrop"
          @click="fileInput?.click()"
          class="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed
                 py-12 cursor-pointer transition-colors duration-150 select-none"
          :class="dragOver
            ? 'border-accent/60 bg-accent/[0.05]'
            : 'border-white/[0.10] hover:border-white/[0.18] bg-white/[0.02]'"
        >
          <input ref="fileInput" type="file" accept=".csv" class="hidden" @change="e => handleFile(e.target.files[0])" />
          <Upload :size="22" class="text-fg-subtle/40" />
          <div class="text-center">
            <p class="text-sm text-fg-subtle">
              Перетащите CSV или <span class="text-accent">выберите файл</span>
            </p>
            <p class="text-xs text-fg-subtle/40 mt-1">Кодировка UTF-8, расширение .csv</p>
          </div>
        </div>

        <!-- format hint -->
        <div class="rounded-lg border border-white/[0.10] bg-bg p-4">
          <p class="text-xs text-fg-subtle mb-3 flex items-center gap-1.5">
            <FileText :size="12" /> Ожидаемый формат
          </p>
          <div class="rounded-md overflow-hidden border border-white/[0.08] mb-3">
            <div class="px-3 py-1.5 bg-white/[0.04] border-b border-white/[0.06]">
              <span class="text-xs text-fg-subtle/70 font-mono">services.csv</span>
            </div>
            <pre class="text-xs font-mono leading-relaxed px-3 py-3 select-all"><span class="text-fg-subtle/40">name,category,rule_type,rule_value</span>
<span class="text-fg">Telegram,Мессенджеры,domain,telegram.org</span>
<span class="text-fg">Telegram,Мессенджеры,domain,t.me</span>
<span class="text-fg">YouTube,Видео,url,https://youtube.com</span>
<span class="text-fg">8.8.8.8 DNS,DNS,ip,8.8.8.8</span>
<span class="text-fg-subtle/60">Slack,Работа,,</span></pre>
          </div>
          <p class="text-xs text-fg-subtle/60">
            Несколько правил у одного сервиса — несколько строк с одинаковыми <span class="font-mono text-fg-subtle">name</span> и <span class="font-mono text-fg-subtle">category</span>.
            Колонки <span class="font-mono text-fg-subtle">rule_type</span> / <span class="font-mono text-fg-subtle">rule_value</span> необязательны.
          </p>
        </div>
      </div>

      <!-- STEP: preview -->
      <div v-else class="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-5">

        <!-- will be added -->
        <div>
          <div class="flex items-center gap-2 mb-2">
            <CheckCircle2 :size="13" class="text-emerald-400 shrink-0" />
            <span class="text-xs font-medium text-fg">Будет добавлено</span>
            <span class="text-xs text-fg-subtle/70 tabular-nums">{{ toCreate.length }}</span>
          </div>
          <div v-if="!toCreate.length" class="text-xs text-fg-subtle/40 px-1">
            Нет новых сервисов для добавления
          </div>
          <div v-else class="flex flex-col gap-1">
            <div
              v-for="svc in toCreate"
              :key="`${svc.name}::${svc.category}`"
              class="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-950/25 border border-emerald-900/30"
            >
              <span class="text-xs text-fg flex-1 truncate">{{ svc.name }}</span>
              <span class="text-xs text-fg-subtle/60 truncate max-w-[120px]">{{ svc.category }}</span>
              <span class="text-xs text-fg-subtle/50 tabular-nums shrink-0">
                {{ svc.rules.length }} {{ svc.rules.length === 1 ? 'правило' : 'правил' }}
              </span>
            </div>
          </div>
        </div>

        <!-- skipped -->
        <div v-if="skipped.length">
          <div class="flex items-center gap-2 mb-2">
            <Info :size="13" class="text-blue-400 shrink-0" />
            <span class="text-xs font-medium text-fg">Пропущены</span>
            <span class="text-xs text-fg-subtle/70 tabular-nums">{{ skipped.length }}</span>
          </div>
          <div class="flex flex-col gap-1">
            <div
              v-for="svc in skipped"
              :key="`${svc.name}::${svc.category}`"
              class="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]"
            >
              <span class="text-xs text-fg-subtle/60 flex-1 truncate">{{ svc.name }}</span>
              <span class="text-xs text-fg-subtle/50 truncate max-w-[120px]">{{ svc.category }}</span>
              <span class="text-xs text-fg-subtle/50 shrink-0 italic">{{ svc.reason }}</span>
            </div>
          </div>
        </div>

        <!-- invalid rows -->
        <div v-if="invalid.length">
          <div class="flex items-center gap-2 mb-2">
            <AlertCircle :size="13" class="text-red-400 shrink-0" />
            <span class="text-xs font-medium text-fg">Ошибки</span>
            <span class="text-xs text-fg-subtle/70 tabular-nums">{{ invalid.length }}</span>
          </div>
          <div class="flex flex-col gap-1">
            <div
              v-for="row in invalid"
              :key="row.row"
              class="flex items-start gap-2.5 px-3 py-2 rounded-lg bg-red-950/20 border border-red-900/30"
            >
              <span class="text-xs text-red-400/80 shrink-0 font-mono pt-0.5">стр. {{ row.row }}</span>
              <span class="text-xs text-red-300/70">{{ row.reason }}</span>
            </div>
          </div>
        </div>

        <p v-if="importError" class="text-xs text-red-400">{{ importError }}</p>
      </div>

      <div class="h-px bg-white/[0.06] mx-6 shrink-0" />

      <!-- footer -->
      <div class="flex items-center justify-between px-6 py-4 shrink-0">
        <button
          v-if="step === 'preview'"
          @click="step = 'pick'"
          class="text-xs text-fg-subtle hover:text-fg transition-colors"
        >
          Загрузить другой файл
        </button>
        <div v-else />

        <div class="flex items-center gap-2">
          <button
            @click="emit('update:open', false)"
            class="h-8 px-4 rounded-md text-xs border border-white/[0.08] text-fg-subtle
                   hover:text-fg hover:border-white/20 transition-colors"
          >
            Отмена
          </button>
          <button
            v-if="step === 'preview'"
            @click="doImport"
            :disabled="importing || !toCreate.length"
            class="h-8 px-4 rounded-md text-xs font-medium text-[#1c1917] disabled:opacity-50 transition-opacity"
            style="background: linear-gradient(135deg, #c4683a, #d4785a)"
          >
            {{ importing ? 'Импорт...' : `Добавить ${toCreate.length}` }}
          </button>
        </div>
      </div>

    </DialogContent>
  </Dialog>
</template>
