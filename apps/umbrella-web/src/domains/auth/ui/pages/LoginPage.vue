<script setup>
import { useAuthStore } from '@/domains/auth/store'

const authStore = useAuthStore()
const router    = useRouter()
const route     = useRoute()

const email     = ref('')
const password  = ref('')
const formError = ref('')

async function handleSubmit() {
  formError.value = ''
  try {
    await authStore.login(email.value, password.value)
    router.push(route.query.redirect || '/')
  } catch (err) {
    formError.value = err.message ?? 'Не удалось выполнить вход'
  }
}
</script>

<template>
  <EmptyLayout>
    <div class="relative min-h-screen flex items-center justify-center px-4 overflow-hidden">

      <!-- фоновый акцентный glow -->
      <div class="pointer-events-none absolute inset-0 overflow-hidden">
        <div class="absolute -top-48 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full opacity-[0.07]"
             style="background: radial-gradient(ellipse at center, #d4785a 0%, transparent 70%)" />
      </div>

      <!-- тонкая сетка -->
      <div class="pointer-events-none absolute inset-0 opacity-[0.025]"
           style="background-image: linear-gradient(#e8dfd4 1px, transparent 1px), linear-gradient(90deg, #e8dfd4 1px, transparent 1px); background-size: 40px 40px" />

      <div class="relative w-full max-w-[400px] flex flex-col gap-10">

        <!-- brand -->
        <div class="flex flex-col items-center gap-4">
          <div class="relative flex items-center justify-center w-16 h-16">
            <!-- glow -->
            <div class="absolute inset-0 rounded-full opacity-20 blur-2xl"
                 style="background: radial-gradient(circle, #d4785a, transparent 70%)" />
            <!-- animated shield -->
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" class="relative">
              <path
                d="M24 4 L42 11 L42 24 C42 33.5 34 41 24 44 C14 41 6 33.5 6 24 L6 11 Z"
                stroke="url(#shieldGrad)"
                stroke-width="1.5"
                stroke-linejoin="round"
                stroke-dasharray="130"
                stroke-dashoffset="130"
                style="animation: draw-line 1.8s cubic-bezier(0.4,0,0.2,1) 0.2s forwards"
              />
              <defs>
                <linearGradient id="shieldGrad" x1="6" y1="4" x2="42" y2="44" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#e08d72"/>
                  <stop offset="100%" stop-color="#b5603e"/>
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div class="text-center">
            <h1 class="text-[32px] text-fg font-serif font-normal leading-none tracking-tight">
              Umbrella
            </h1>
            <p class="text-sm text-fg-subtle mt-2 leading-relaxed">
              Консоль управления конечными устройствами
            </p>
          </div>
        </div>

        <!-- card -->
        <div class="bg-bg-raised rounded-2xl border border-white/[0.06] overflow-hidden"
             style="box-shadow: 0 0 0 1px rgba(255,255,255,0.03), 0 24px 48px rgba(0,0,0,0.4)">

          <!-- card header stripe -->
          <div class="h-px w-full" style="background: linear-gradient(90deg, transparent, rgba(212,120,90,0.4), transparent)" />

          <form class="p-8 flex flex-col gap-5" @submit.prevent="handleSubmit">

            <!-- error banner -->
            <div v-if="formError"
                 class="flex items-start gap-2.5 text-sm text-red-400 bg-red-950/30 border border-red-900/30 rounded-xl px-4 py-3">
              <svg class="w-4 h-4 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                <path d="M8 5v3.5M8 11v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <span>{{ formError }}</span>
            </div>

            <!-- email -->
            <div class="flex flex-col gap-2">
              <label class="text-[11px] font-semibold uppercase tracking-[0.1em] text-fg-subtle select-none">
                Почта
              </label>
              <Input
                v-model="email"
                type="email"
                autocomplete="email"
                placeholder="name@company.com"
                class="h-10 bg-bg border-white/[0.08] text-fg placeholder:text-fg-subtle/50
                       focus-visible:border-accent/50 focus-visible:ring-accent/20"
              />
            </div>

            <!-- password -->
            <div class="flex flex-col gap-2">
              <label class="text-[11px] font-semibold uppercase tracking-[0.1em] text-fg-subtle select-none">
                Пароль
              </label>
              <Input
                v-model="password"
                type="password"
                autocomplete="current-password"
                placeholder="••••••••"
                class="h-10 bg-bg border-white/[0.08] text-fg placeholder:text-fg-subtle/50
                       focus-visible:border-accent/50 focus-visible:ring-accent/20"
              />
            </div>

            <!-- submit -->
            <button
              type="submit"
              :disabled="authStore.isLoading"
              class="relative mt-1 h-10 w-full rounded-lg text-sm font-medium
                     text-[#1c1917] transition-all duration-150 overflow-hidden
                     disabled:opacity-60 disabled:cursor-not-allowed
                     hover:brightness-110 active:scale-[0.99]"
              style="background: linear-gradient(135deg, #c4683a 0%, #d4785a 50%, #e08d72 100%)"
            >
              <span v-if="authStore.isLoading" class="flex items-center justify-center gap-2">
                <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="32" stroke-dashoffset="8"/>
                </svg>
                Вход...
              </span>
              <span v-else>Войти</span>
            </button>

          </form>
        </div>

        <!-- footer -->
        <p class="text-center text-xs text-fg-subtle/50">
          Umbrella · Консоль управления · v1.0
        </p>

      </div>
    </div>
  </EmptyLayout>
</template>
