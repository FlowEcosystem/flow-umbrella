<script setup>
import { Check, AlertCircle, RefreshCw } from 'lucide-vue-next'
import { useSettingsPage } from '@/domains/settings/useSettingsPage'

const {
  auth, ROLE_LABELS,
  profileForm, profileLoading, profileError, profileSuccess, profileDirty, submitProfile,
  passwordForm, passwordLoading, passwordError, passwordSuccess,
  passwordMismatch, passwordValid, submitPassword,
} = useSettingsPage()

const userInitials = computed(() => {
  const name = auth.currentUser?.full_name ?? auth.currentUser?.email ?? ''
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'
})

// ── DiceBear ─────────────────────────────────────────────
const STYLES = [
  'adventurer', 'avataaars', 'big-ears', 'bottts',
  'croodles', 'fun-emoji', 'lorelei', 'micah',
  'pixel-art', 'thumbs', 'notionists', 'shapes',
]

const diceSeed = computed(() =>
  auth.currentUser?.email ?? 'umbrella'
)

function diceUrl(style, seed) {
  return `https://api.dicebear.com/9.x/${style}/svg?seed=${encodeURIComponent(seed)}`
}

const randomSeed = ref(diceSeed.value)

function randomize() {
  randomSeed.value = Math.random().toString(36).slice(2)
}

function pickDice(style) {
  profileForm.value.avatar_url = diceUrl(style, randomSeed.value)
}

const isSelected = (style) =>
  profileForm.value.avatar_url === diceUrl(style, randomSeed.value)
</script>

<template>
  <div class="px-8 py-8 max-w-3xl mx-auto w-full">

    <!-- header -->
    <div class="mb-8">
      <h1 class="text-4xl text-fg mb-1.5 leading-tight font-serif font-normal">Настройки</h1>
      <p class="text-sm text-fg-subtle">Профиль и безопасность аккаунта.</p>
    </div>

    <div class="flex flex-col gap-5">

      <!-- profile card -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-6">

        <h2 class="text-sm font-medium text-fg mb-5">Профиль</h2>

        <!-- avatar row -->
        <div class="flex items-center gap-4 mb-6">
          <div class="shrink-0 w-14 h-14 rounded-full overflow-hidden">
            <img
              v-if="profileForm.avatar_url"
              :src="profileForm.avatar_url"
              class="w-full h-full object-cover"
              :alt="userInitials"
            />
            <div v-else
                 class="w-full h-full bg-accent-dim flex items-center justify-center">
              <span class="text-accent text-xl font-medium">{{ userInitials }}</span>
            </div>
          </div>
          <div>
            <p class="text-sm text-fg font-medium">{{ auth.currentUser?.full_name ?? auth.currentUser?.email }}</p>
            <span class="inline-block text-xs text-fg-subtle/60 bg-white/[0.04] border border-white/[0.06]
                         px-2 py-0.5 rounded-full mt-1">
              {{ ROLE_LABELS[auth.currentUser?.role] ?? auth.currentUser?.role }}
            </span>
          </div>
        </div>

        <!-- form -->
        <div class="flex flex-col gap-4">

          <!-- email (read-only) -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-fg-subtle">Email</label>
            <div class="h-9 rounded-md border border-white/[0.06] bg-bg/50 px-3 flex items-center">
              <span class="text-sm text-fg-subtle/60">{{ auth.currentUser?.email }}</span>
            </div>
          </div>

          <!-- full_name -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-fg-subtle">Имя</label>
            <input
              v-model="profileForm.full_name"
              placeholder="Иван Иванов"
              class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                     placeholder:text-fg-subtle/40 focus:outline-none focus:border-white/20 transition-colors"
            />
          </div>

          <!-- avatar picker -->
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label class="text-xs text-fg-subtle">Аватар</label>
              <button
                type="button"
                @click="randomize"
                class="flex items-center gap-1.5 text-xs text-fg-subtle hover:text-fg transition-colors"
              >
                <RefreshCw :size="11" />
                Случайный seed
              </button>
            </div>

            <!-- dicebear grid -->
            <div class="grid grid-cols-6 gap-2">
              <button
                v-for="style in STYLES"
                :key="style"
                type="button"
                @click="pickDice(style)"
                class="relative aspect-square rounded-xl overflow-hidden border-2 transition-all duration-100"
                :class="isSelected(style)
                  ? 'border-accent scale-105'
                  : 'border-transparent hover:border-white/20'"
                :title="style"
              >
                <img
                  :src="diceUrl(style, randomSeed)"
                  :alt="style"
                  class="w-full h-full object-cover bg-white/[0.04]"
                />
                <span v-if="isSelected(style)"
                      class="absolute inset-0 flex items-center justify-center
                             bg-accent/20 backdrop-blur-[1px]">
                  <Check :size="14" class="text-accent" />
                </span>
              </button>

              <!-- clear -->
              <button
                type="button"
                @click="profileForm.avatar_url = ''"
                class="aspect-square rounded-xl border-2 transition-all duration-100 flex items-center justify-center
                       text-fg-subtle/40 text-xs"
                :class="!profileForm.avatar_url
                  ? 'border-white/20 text-fg-subtle'
                  : 'border-transparent hover:border-white/20'"
                title="Без аватара"
              >
                —
              </button>
            </div>

            <!-- custom url -->
            <input
              v-model="profileForm.avatar_url"
              placeholder="или вставьте свой URL..."
              class="h-8 rounded-md border border-white/[0.06] bg-bg px-3 text-xs text-fg
                     placeholder:text-fg-subtle/30 focus:outline-none focus:border-white/20 transition-colors"
            />
          </div>

          <!-- feedback + save -->
          <div class="flex items-center gap-3 pt-1">
            <button
              @click="submitProfile"
              :disabled="profileLoading || !profileDirty"
              class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-colors
                     disabled:opacity-40 disabled:cursor-not-allowed"
              style="background: linear-gradient(135deg, #c4683a, #d4785a)"
            >
              {{ profileLoading ? 'Сохранение...' : 'Сохранить' }}
            </button>

            <Transition
              enter-active-class="transition-all duration-150"
              enter-from-class="opacity-0 translate-x-1"
              leave-active-class="transition-all duration-100"
              leave-to-class="opacity-0"
            >
              <span v-if="profileSuccess" class="flex items-center gap-1.5 text-xs text-emerald-400">
                <Check :size="13" /> Сохранено
              </span>
              <span v-else-if="profileError" class="flex items-center gap-1.5 text-xs text-red-400">
                <AlertCircle :size="13" /> {{ profileError }}
              </span>
            </Transition>
          </div>
        </div>
      </div>

      <!-- security card -->
      <div class="bg-bg-raised border border-white/[0.06] rounded-xl p-6">

        <h2 class="text-sm font-medium text-fg mb-5">Смена пароля</h2>

        <div class="flex flex-col gap-4 max-w-sm">

          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-fg-subtle">Текущий пароль</label>
            <input
              v-model="passwordForm.current"
              type="password"
              autocomplete="current-password"
              class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                     focus:outline-none focus:border-white/20 transition-colors"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-fg-subtle">Новый пароль <span class="opacity-40">(мин. 8 символов)</span></label>
            <input
              v-model="passwordForm.next"
              type="password"
              autocomplete="new-password"
              class="h-9 rounded-md border border-white/[0.08] bg-bg px-3 text-sm text-fg
                     focus:outline-none focus:border-white/20 transition-colors"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-fg-subtle">Повтор нового пароля</label>
            <input
              v-model="passwordForm.confirm"
              type="password"
              autocomplete="new-password"
              class="h-9 rounded-md border transition-colors"
              :class="passwordMismatch
                ? 'border-red-800/60 bg-red-950/20 text-fg px-3 text-sm focus:outline-none'
                : 'border-white/[0.08] bg-bg px-3 text-sm text-fg focus:outline-none focus:border-white/20'"
            />
            <p v-if="passwordMismatch" class="text-xs text-red-400">Пароли не совпадают</p>
          </div>

          <div class="flex items-center gap-3 pt-1">
            <button
              @click="submitPassword"
              :disabled="passwordLoading || !passwordValid"
              class="h-9 px-4 rounded-md text-sm font-medium text-[#1c1917] transition-colors
                     disabled:opacity-40 disabled:cursor-not-allowed"
              style="background: linear-gradient(135deg, #c4683a, #d4785a)"
            >
              {{ passwordLoading ? 'Смена...' : 'Сменить пароль' }}
            </button>

            <Transition
              enter-active-class="transition-all duration-150"
              enter-from-class="opacity-0 translate-x-1"
              leave-active-class="transition-all duration-100"
              leave-to-class="opacity-0"
            >
              <span v-if="passwordSuccess" class="flex items-center gap-1.5 text-xs text-emerald-400">
                <Check :size="13" /> Пароль изменён
              </span>
              <span v-else-if="passwordError" class="flex items-center gap-1.5 text-xs text-red-400">
                <AlertCircle :size="13" /> {{ passwordError }}
              </span>
            </Transition>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
