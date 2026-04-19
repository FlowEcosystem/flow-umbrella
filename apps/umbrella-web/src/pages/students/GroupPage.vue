<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <h1 class="text-2xl font-semibold tracking-tight">Группы</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Группы связывают студентов, расписание, дисциплины, домашние задания и показатели
        успеваемости.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Состав группы</div>
        <p class="mt-2 text-sm text-base-content/70">Список студентов, кураторы и учебный статус.</p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Статистика</div>
        <p class="mt-2 text-sm text-base-content/70">
          Средний балл, задолженности, активные домашние задания.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Планирование</div>
        <p class="mt-2 text-sm text-base-content/70">
          Привязка расписания, дисциплин и преподавателей к группе.
        </p>
      </article>
    </div>
  </section>
</template>
