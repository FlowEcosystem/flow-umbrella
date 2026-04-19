<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <h1 class="text-2xl font-semibold tracking-tight">Дисциплины</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Справочник дисциплин должен быть основой для расписания, методпакетов, домашних заданий и
        ведомостей.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Учебная программа</div>
        <p class="mt-2 text-sm text-base-content/70">
          Название, период, нагрузка, связь с группами и преподавателями.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Материалы</div>
        <p class="mt-2 text-sm text-base-content/70">
          Привязка методпакетов, тем и базовых файлов к дисциплине.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Оценивание</div>
        <p class="mt-2 text-sm text-base-content/70">
          Параметры ведомости, шкалы оценок и контрольные точки.
        </p>
      </article>
    </div>
  </section>
</template>
