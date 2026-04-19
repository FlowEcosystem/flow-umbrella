<script setup>
const authStore = useAuthStore()

const statuses = ['Черновик', 'Опубликовано', 'На проверке', 'Возвращено', 'Отклонено', 'Принято']

const focusAreas = computed(() => {
  if (authStore.role === 'student') {
    return ['Получение задания', 'Загрузка решения', 'Отслеживание статуса проверки']
  }

  if (authStore.role === 'teacher') {
    return ['Публикация ДЗ', 'Проверка и комментарии', 'Повторная отправка и возврат']
  }

  return ['Контроль заданий по филиалу', 'Разрешение конфликтов', 'Просмотр истории действий']
})
</script>

<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <h1 class="text-2xl font-semibold tracking-tight">Домашние задания</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Центральный модуль учебного цикла: постановка, сдача, проверка, возврат и итоговая
        фиксация результата.
      </p>
    </div>

    <div class="grid gap-4 xl:grid-cols-[1.5fr,1fr]">
      <div class="grid gap-4 md:grid-cols-3">
        <article
          v-for="item in focusAreas"
          :key="item"
          class="rounded-2xl border border-base-300 bg-base-100 p-4 text-sm shadow-sm"
        >
          {{ item }}
        </article>
      </div>

      <div class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Базовый workflow</div>
        <div class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="status in statuses"
            :key="status"
            class="badge badge-outline rounded-xl px-3 py-3"
          >
            {{ status }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>
