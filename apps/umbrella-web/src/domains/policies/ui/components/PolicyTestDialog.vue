<script setup>
import { X, Info } from 'lucide-vue-next'
import { usePoliciesStore } from '@/domains/policies/store'

const props = defineProps({
  open: { type: Boolean, required: true },
})
const emit = defineEmits(['update:open'])

const store = usePoliciesStore()
const query = ref('')

// --- input type ---
const inputType = computed(() => {
  const t = query.value.trim()
  if (!t) return null
  if (/^https?:\/\//.test(t)) return 'url'
  if (/^(\d{1,3}\.){3}\d{1,3}(\/\d+)?$/.test(t)) return 'ip'
  if (t.includes('.') && !t.includes(' ')) return 'domain'
  return 'keyword'
})

const TYPE_STYLES = {
  url:     'border-blue-800/50 text-blue-400',
  ip:      'border-cyan-800/50 text-cyan-400',
  domain:  'border-violet-800/50 text-violet-400',
  keyword: 'border-white/20 text-fg-subtle/60',
}
const TYPE_LABELS = { url: 'URL', ip: 'IP', domain: 'домен', keyword: 'поиск' }

// --- matching ---
function ipToNum(ip) {
  return ip.split('.').reduce((acc, o) => ((acc << 8) + parseInt(o)) >>> 0, 0)
}
function exactMatchRule(input, rule) {
  const val = rule.value.toLowerCase().trim()
  const inp = input.toLowerCase().trim()
  if (rule.type === 'url') {
    return inp.startsWith('http') && inp.startsWith(val)
  }
  if (rule.type === 'domain') {
    let domain = inp
    if (inp.startsWith('http')) { try { domain = new URL(inp).hostname } catch { return false } }
    return val.startsWith('*.') ? domain === val.slice(2) || domain.endsWith('.' + val.slice(2))
                                : domain === val || domain.endsWith('.' + val)
  }
  if (rule.type === 'ip') {
    if (!/^(\d{1,3}\.){3}\d{1,3}/.test(inp)) return false
    const ip = inp.split('/')[0]
    if (!val.includes('/')) return ip === val
    const [range, bits] = val.split('/')
    const mask = (0xFFFFFFFF << (32 - parseInt(bits))) >>> 0
    return (ipToNum(ip) & mask) === (ipToNum(range) & mask)
  }
  return false
}

// --- unified results ---
const results = computed(() => {
  const q = query.value.trim()
  if (q.length < 2) return []
  const needle = q.toLowerCase()

  return store.items
    .map(policy => {
      const matches = []

      for (const svc of policy.services ?? []) {
        if (svc.name.toLowerCase().includes(needle)) {
          matches.push({ label: svc.name, kind: 'service' })
        } else {
          for (const rule of svc.rules ?? []) {
            if (rule.value.toLowerCase().includes(needle) || exactMatchRule(q, rule)) {
              matches.push({ label: rule.value, kind: 'rule', service: svc.name })
            }
          }
        }
      }

      for (const rule of policy.custom_rules ?? []) {
        if (rule.value.toLowerCase().includes(needle) || exactMatchRule(q, rule)) {
          matches.push({ label: rule.value, kind: 'rule' })
        }
      }

      return matches.length ? { policy, matches } : null
    })
    .filter(Boolean)
    .sort((a, b) => {
      if (a.policy.is_active !== b.policy.is_active) return a.policy.is_active ? -1 : 1
      if (a.policy.action !== b.policy.action) return a.policy.action === 'block' ? -1 : 1
      return 0
    })
})

const blockCount    = computed(() => results.value.filter(r => r.policy.is_active && r.policy.action === 'block').length)
const allowCount    = computed(() => results.value.filter(r => r.policy.is_active && r.policy.action === 'allow').length)
const inactiveCount = computed(() => results.value.filter(r => !r.policy.is_active).length)

const EXAMPLES = [
  { label: 'steam',          style: 'border-amber-800/50 text-amber-400 hover:border-amber-700/70 hover:bg-amber-950/20' },
  { label: 't.me',           style: 'border-violet-800/50 text-violet-400 hover:border-violet-700/70 hover:bg-violet-950/20' },
  { label: 'youtube.com',    style: 'border-red-800/50 text-red-400 hover:border-red-700/70 hover:bg-red-950/20' },
  { label: '192.168.0.0/16', style: 'border-cyan-800/50 text-cyan-400 hover:border-cyan-700/70 hover:bg-cyan-950/20' },
]

watch(() => props.open, v => { if (!v) query.value = '' })
</script>

<template>
  <Dialog :open="open" @update:open="v => !v && emit('update:open', false)">
    <DialogContent
      :show-close-button="false"
      class="max-w-lg p-0 border-white/8 bg-bg-raised gap-0 flex flex-col max-h-[80vh]"
    >

      <!-- input section -->
      <div class="px-5 pt-5 pb-4 shrink-0">
        <div class="flex items-center justify-between mb-4">
          <DialogTitle class="text-sm font-medium text-fg">Тест политик</DialogTitle>
          <button @click="emit('update:open', false)" class="text-fg-subtle hover:text-fg transition-colors">
            <X :size="15" />
          </button>
        </div>

        <div class="relative">
          <input
            v-model="query"
            placeholder="steam, t.me, https://site.com, 10.0.0.1"
            class="h-10 w-full rounded-lg border border-white/10 bg-bg px-3.5 pr-20 text-sm text-fg
                   placeholder:text-fg-subtle/35 focus:outline-none focus:border-white/20 transition-colors"
            autofocus
          />
          <span
            v-if="inputType"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[11px] px-1.5 py-0.5
                   rounded border bg-bg"
            :class="TYPE_STYLES[inputType]"
          >
            {{ TYPE_LABELS[inputType] }}
          </span>
        </div>
      </div>

      <div class="h-px bg-white/6 shrink-0" />

      <!-- results area -->
      <div class="flex-1 overflow-y-auto">

        <!-- empty / hint -->
        <div v-if="!query.trim()" class="flex flex-col items-center gap-4 py-12 px-6">
          <p class="text-sm text-fg-subtle/50">Введите название сервиса, домен, URL или IP</p>
          <div class="flex flex-wrap justify-center gap-1.5">
            <button
              v-for="ex in EXAMPLES" :key="ex.label"
              @click="query = ex.label"
              class="text-xs px-2.5 py-1 rounded-md border transition-colors"
              :class="ex.style"
            >
              {{ ex.label }}
            </button>
          </div>
        </div>

        <!-- too short -->
        <div v-else-if="query.trim().length < 2"
             class="flex items-center justify-center py-12">
          <p class="text-sm text-fg-subtle/50">Введите минимум 2 символа</p>
        </div>

        <!-- no results -->
        <div v-else-if="!results.length"
             class="flex flex-col items-center gap-2 py-12">
          <Info :size="18" class="text-fg-subtle/30" />
          <p class="text-sm text-fg-subtle/60">Ни одна политика не совпадает</p>
        </div>

        <!-- results -->
        <template v-else>

          <!-- summary bar -->
          <div class="px-5 py-2.5 flex items-center gap-1.5 border-b border-white/[0.04] text-xs">
            <span class="text-fg-subtle/60">{{ results.length }} совп.</span>
            <template v-if="blockCount">
              <span class="text-fg-subtle/30">·</span>
              <span class="text-red-400/80">{{ blockCount }} блокируют</span>
            </template>
            <template v-if="allowCount">
              <span class="text-fg-subtle/30">·</span>
              <span class="text-emerald-400/80">{{ allowCount }} разрешают</span>
            </template>
            <template v-if="inactiveCount">
              <span class="text-fg-subtle/30">·</span>
              <span class="text-fg-subtle/40">{{ inactiveCount }} неакт.</span>
            </template>
          </div>

          <!-- policy rows -->
          <div class="divide-y divide-white/[0.04]">
            <div
              v-for="hit in results"
              :key="hit.policy.id"
              class="px-5 py-3.5 flex items-start gap-3 transition-opacity"
              :class="!hit.policy.is_active ? 'opacity-40' : ''"
            >
              <!-- action dot -->
              <div
                class="w-2 h-2 rounded-full mt-1.5 shrink-0"
                :class="hit.policy.action === 'block' ? 'bg-red-400' : 'bg-emerald-400'"
              />

              <!-- name + chips -->
              <div class="flex-1 min-w-0">
                <p class="text-sm text-fg leading-tight">{{ hit.policy.name }}</p>
                <div class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="m in hit.matches.slice(0, 7)"
                    :key="m.label"
                    class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border"
                    :class="m.kind === 'service'
                      ? 'border-white/[0.16] text-fg-subtle bg-white/[0.07]'
                      : 'border-white/[0.20] text-fg/80 font-mono bg-white/[0.07]'"
                  >
                    <span v-if="m.kind === 'service'" class="text-fg-subtle/60 not-italic text-[10px] font-sans">сервис</span>
                    {{ m.label }}
                    <span v-if="m.service" class="font-sans not-italic text-fg-subtle/40"> · </span>
                    <span v-if="m.service" class="font-sans not-italic text-blue-300/70">{{ m.service }}</span>
                  </span>
                  <span v-if="hit.matches.length > 7"
                        class="text-xs text-fg-subtle/50 px-1 self-center">
                    +{{ hit.matches.length - 7 }}
                  </span>
                </div>
              </div>

              <!-- action label -->
              <div class="shrink-0 text-right pt-0.5">
                <span
                  class="text-xs font-medium"
                  :class="hit.policy.action === 'block' ? 'text-red-400' : 'text-emerald-400'"
                >
                  {{ hit.policy.action === 'block' ? 'блок' : 'разреш.' }}
                </span>
                <p v-if="!hit.policy.is_active" class="text-[11px] text-fg-subtle/40 mt-0.5">неактивна</p>
              </div>
            </div>
          </div>

        </template>
      </div>

    </DialogContent>
  </Dialog>
</template>
