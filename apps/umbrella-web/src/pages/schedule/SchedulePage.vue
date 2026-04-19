<script setup>
const authStore = useAuthStore()

const capabilities = computed(() => {
  if (authStore.role === 'student') {
    return ['Просмотр личного расписания', 'Аудитории и преподаватели', 'Ближайшие пары и переносы']
  }

  if (authStore.role === 'teacher') {
    return ['Просмотр своего расписания', 'Закрепленные группы', 'Контроль учебной нагрузки']
  }

  return ['Формирование расписания', 'Управление кабинетами и слотами', 'Контроль по филиалу']
})
</script>

<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <h1 class="text-2xl font-semibold tracking-tight">Расписание</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Модуль должен поддерживать личное, преподавательское и административное представление
        расписания.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <article
        v-for="capability in capabilities"
        :key="capability"
        class="rounded-2xl border border-base-300 bg-base-100 p-4 text-sm shadow-sm"
      >
        {{ capability }}
      </article>
    </div>
  </section>
</template>
