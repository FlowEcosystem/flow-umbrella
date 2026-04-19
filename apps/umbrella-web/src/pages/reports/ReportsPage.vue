<template>
  <section class="max-w-6xl mx-auto space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <div class="flex items-start gap-4">
        <div
          class="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-secondary/10 text-secondary"
        >
          <ChartColumnBig class="size-7" />
        </div>

        <div>
          <h1 class="text-2xl font-semibold tracking-tight">Отчеты и статистика филиала</h1>
          <p class="mt-2 text-sm text-base-content/70">
            Здесь должен жить аналитический контур для менеджера учебного процесса и директора:
            сводная успеваемость, динамика групп, выгрузки и контрольные показатели филиала.
          </p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Успеваемость</div>
        <p class="mt-2 text-sm text-base-content/70">
          Отчеты по периодам, группам, дисциплинам и преподавателям.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Операционные выгрузки</div>
        <p class="mt-2 text-sm text-base-content/70">
          Экспорт в табличные форматы и сбор статистики по филиалу.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Контроль доступа</div>
        <p class="mt-2 text-sm text-base-content/70">
          Просмотр критичных действий и влияния impersonation на аудит.
        </p>
      </article>
    </div>
  </section>
</template>
