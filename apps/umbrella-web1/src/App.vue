<script setup>
import { useAuthStore } from '@/domains/auth/store'

const auth = useAuthStore()

const LINES = [
  { delay: 0,    text: 'Umbrella Management Console v1.0' },
  { delay: 400,  text: 'Загрузка конфигурации системы...' },
  { delay: 1000, text: 'Проверка токена сессии...' },
  { delay: 1800, text: 'Запрос профиля пользователя...' },
]

const visibleCount = ref(0)
const cursor       = ref(true)

onMounted(() => {
  LINES.forEach((line, i) => {
    setTimeout(() => { visibleCount.value = i + 1 }, line.delay)
  })

  const cursorTimer = setInterval(() => { cursor.value = !cursor.value }, 530)
  onUnmounted(() => clearInterval(cursorTimer))
})
</script>

<template>
  <!-- boot overlay — fixed on top, fades out when ready -->
  <Transition name="fade">
    <div v-if="!auth.ready"
         class="fixed inset-0 z-[100] bg-bg overflow-hidden flex flex-col">

      <!-- grid texture -->
      <div class="pointer-events-none absolute inset-0 opacity-[0.03]"
           style="background-image: linear-gradient(#e8dfd4 1px, transparent 1px), linear-gradient(90deg, #e8dfd4 1px, transparent 1px); background-size: 48px 48px" />

      <!-- accent glow -->
      <div class="pointer-events-none absolute -top-32 -left-32 w-[500px] h-[500px] rounded-full opacity-[0.04]"
           style="background: radial-gradient(circle, #d4785a, transparent 70%)" />

      <!-- corner marks -->
      <div class="absolute top-6 left-6 w-4 h-4 border-t border-l border-fg-subtle/20" />
      <div class="absolute top-6 right-6 w-4 h-4 border-t border-r border-fg-subtle/20" />
      <div class="absolute bottom-6 left-6 w-4 h-4 border-b border-l border-fg-subtle/20" />
      <div class="absolute bottom-6 right-6 w-4 h-4 border-b border-r border-fg-subtle/20" />

      <!-- top bar -->
      <div class="relative flex items-center gap-3 px-8 pt-8">
        <svg width="16" height="16" viewBox="0 0 48 48" fill="none" class="shrink-0">
          <path d="M24 4 L42 11 L42 24 C42 33.5 34 41 24 44 C14 41 6 33.5 6 24 L6 11 Z"
                stroke="#d4785a" stroke-width="2" stroke-linejoin="round" />
        </svg>
        <span class="text-xs text-fg-subtle/50 font-mono tracking-widest uppercase">Umbrella · System Boot</span>
        <div class="flex-1 h-px bg-white/[0.05] ml-2" />
        <span class="text-xs text-fg-subtle/30 font-mono">
          {{ new Date().toISOString().slice(0, 19).replace('T', ' ') }}
        </span>
      </div>

      <!-- terminal block -->
      <div class="relative flex-1 flex flex-col items-center justify-center">
        <div class="w-full max-w-md px-8">

          <!-- shield -->
          <div class="mb-10">
            <svg width="44" height="44" viewBox="0 0 48 48" fill="none">
              <path
                d="M24 4 L42 11 L42 24 C42 33.5 34 41 24 44 C14 41 6 33.5 6 24 L6 11 Z"
                stroke="url(#bootGrad)"
                stroke-width="1.5"
                stroke-linejoin="round"
                stroke-dasharray="130"
                stroke-dashoffset="130"
                style="animation: draw-line 1.6s cubic-bezier(0.4,0,0.2,1) 0.1s forwards"
              />
              <defs>
                <linearGradient id="bootGrad" x1="6" y1="4" x2="42" y2="44" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#e08d72"/>
                  <stop offset="100%" stop-color="#b5603e"/>
                </linearGradient>
              </defs>
            </svg>
          </div>

          <!-- terminal lines -->
          <div class="flex flex-col gap-2.5 font-mono">
            <TransitionGroup name="line">
              <div
                v-for="(line, i) in LINES.slice(0, visibleCount)"
                :key="i"
                class="flex items-baseline gap-3 text-sm"
              >
                <span class="text-accent/70 shrink-0 select-none">›</span>
                <span :class="i === 0 ? 'text-fg/90' : 'text-fg-subtle'">{{ line.text }}</span>
                <span
                  v-if="i === visibleCount - 1"
                  class="inline-block w-1.5 h-[1em] bg-accent/70 ml-0.5 translate-y-[1px] transition-opacity duration-75"
                  :class="cursor ? 'opacity-100' : 'opacity-0'"
                />
              </div>
            </TransitionGroup>
          </div>

        </div>
      </div>

      <!-- bottom status bar -->
      <div class="relative flex items-center justify-between px-8 pb-8">
        <span class="text-xs text-fg-subtle/30 font-mono">SEC-CONSOLE</span>
        <div class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-accent/50"
                style="animation: pulse-dot 1.6s ease-in-out infinite" />
          <span class="text-xs text-fg-subtle/40 font-mono">инициализация</span>
        </div>
      </div>

    </div>
  </Transition>

  <!-- app — always mounted, router handles layout -->
  <RouterView />
</template>
