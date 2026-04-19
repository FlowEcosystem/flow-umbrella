<script setup>
import { getRoleLabel } from '@/config/rbac'
import { useAuthStore } from '@/stores/auth.store'

const authStore = useAuthStore()

const scopes = computed(() => {
  if (authStore.role === 'student') {
    return ['Просмотр методпакетов', 'Скачивание материалов', 'Навигация по дисциплинам']
  }

  if (authStore.role === 'teacher') {
    return ['Публикация материалов', 'Обновление методпакетов', 'Контроль актуальности контента']
  }

  return ['Управление библиотекой материалов', 'Контроль доступа по филиалам', 'Массовые обновления']
})
</script>

<template>
  <section class="max-w-6xl mx-auto space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <div class="flex items-start gap-4">
        <div class="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <LibraryBig class="size-7" />
        </div>

        <div class="space-y-3">
          <div>
            <h1 class="text-2xl font-semibold tracking-tight">Методпакеты</h1>
            <p class="mt-2 text-sm text-base-content/70">
              Модуль для хранения и выдачи учебных материалов. Доступный сценарий зависит от роли
              пользователя.
            </p>
          </div>

          <div class="badge badge-outline rounded-xl px-3 py-3">
            {{ getRoleLabel(authStore.role) }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <article
        v-for="scope in scopes"
        :key="scope"
        class="rounded-2xl border border-base-300 bg-base-100 p-4 text-sm shadow-sm"
      >
        {{ scope }}
      </article>
    </div>
  </section>
</template>
