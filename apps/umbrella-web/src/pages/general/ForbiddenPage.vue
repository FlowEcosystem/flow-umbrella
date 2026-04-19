<template>
  <section class="max-w-3xl mx-auto rounded-3xl border border-base-300 bg-base-100 p-8 shadow-sm">
    <div class="flex items-start gap-4">
      <div class="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-error/10 text-error">
        <ShieldAlert class="size-7" />
      </div>

      <div class="space-y-3">
        <div>
          <h1 class="text-2xl font-semibold tracking-tight">Доступ ограничен</h1>
          <p class="mt-2 text-sm text-base-content/70">
            У текущей роли нет прав на просмотр этого раздела. Доступ к модулям системы
            определяется ролями и матрицей разрешений.
          </p>
        </div>

        <div class="rounded-2xl border border-base-300 bg-base-200/50 p-4 text-sm text-base-content/70">
          Если доступ должен быть открыт, это уже задача менеджера учебного процесса или
          директора: они управляют правами и ролями пользователей.
        </div>

        <div class="flex flex-wrap gap-3">
          <RouterLink to="/" class="btn btn-primary rounded-2xl">На главную</RouterLink>
          <RouterLink to="/settings" class="btn btn-ghost rounded-2xl">Настройки</RouterLink>
        </div>
      </div>
    </div>
  </section>
</template>
