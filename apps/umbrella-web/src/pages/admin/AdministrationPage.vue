<template>
  <section class="max-w-6xl mx-auto space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <div class="flex items-start gap-4">
        <div class="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-warning/10 text-warning">
          <ShieldCheck class="size-7" />
        </div>

        <div>
          <h1 class="text-2xl font-semibold tracking-tight">Администрирование</h1>
          <p class="mt-2 text-sm text-base-content/70">
            Административный контур объединяет управление сущностями колледжа, правами доступа,
            расписанием, impersonation и аудитом.
          </p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Пользователи</div>
        <p class="mt-2 text-sm text-base-content/70">
          Назначение ролей, блокировка, перевод между филиалами и управление доступами.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Расписание</div>
        <p class="mt-2 text-sm text-base-content/70">
          Формирование сетки занятий, кабинетов и распределение нагрузки.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Impersonation</div>
        <p class="mt-2 text-sm text-base-content/70">
          Работа от лица студента или преподавателя только через журналируемый сценарий.
        </p>
      </article>

      <article class="rounded-2xl border border-base-300 bg-base-100 p-4 shadow-sm">
        <div class="text-sm font-semibold">Audit log</div>
        <p class="mt-2 text-sm text-base-content/70">
          История критичных действий, отзыв доступов и подтверждение опасных операций.
        </p>
      </article>
    </div>
  </section>
</template>
