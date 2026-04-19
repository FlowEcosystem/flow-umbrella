<template>
  <section class="mx-auto max-w-3xl rounded-3xl border border-base-300 bg-base-100 p-8 text-center shadow-sm">
    <div class="mx-auto flex size-16 items-center justify-center rounded-2xl bg-base-200 text-base-content/70">
      <MapPinned class="size-8" />
    </div>
    <h1 class="mt-5 text-3xl font-semibold tracking-tight">Страница не найдена</h1>
    <p class="mt-3 text-sm text-base-content/70">
      Маршрут отсутствует в текущей архитектуре приложения или был перенесен в другой модуль.
    </p>

    <div class="mt-6 flex justify-center gap-3">
      <RouterLink to="/" class="btn btn-primary rounded-2xl">На главную</RouterLink>
      <RouterLink to="/settings" class="btn btn-ghost rounded-2xl">Настройки</RouterLink>
    </div>
  </section>
</template>
