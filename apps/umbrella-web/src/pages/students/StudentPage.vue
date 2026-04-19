<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <h1 class="text-2xl font-semibold tracking-tight">Студенты</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Карточки студентов, состав контингента, связь с группами, успеваемостью и домашними
        заданиями.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Карточка студента</div>
        <p class="mt-2 text-sm text-base-content/70">
          Профиль, группа, статус обучения, контактные данные и учебная история.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Учебный прогресс</div>
        <p class="mt-2 text-sm text-base-content/70">
          Оценки, задолженности, статистика посещения и история заданий.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Операции менеджера</div>
        <p class="mt-2 text-sm text-base-content/70">
          Переводы, доступы, блокировки и администрирование карточки.
        </p>
      </article>
    </div>
  </section>
</template>
