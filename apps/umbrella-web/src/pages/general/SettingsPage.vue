<script setup>
import { getApiBaseUrl } from '@/api/http'

const authStore = useAuthStore()
</script>

<template>
  <section class="mx-auto max-w-4xl space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <h1 class="text-2xl font-semibold tracking-tight">Настройки и состояние системы</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Техническая страница для контроля текущей сессии и конфигурации API.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Сессия</div>
        <div class="mt-3 space-y-2 text-sm text-base-content/70">
          <p>Статус: {{ authStore.isAuthenticated ? 'активна' : 'не установлена' }}</p>
          <p>Роль: {{ authStore.roleLabel }}</p>
          <p>Пользователь: {{ authStore.displayName }}</p>
        </div>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">API</div>
        <div class="mt-3 space-y-2 text-sm text-base-content/70">
          <p>Base URL: {{ getApiBaseUrl() }}</p>
          <p>Ошибки сессии: {{ authStore.error || 'нет' }}</p>
        </div>
      </article>
    </div>
  </section>
</template>
