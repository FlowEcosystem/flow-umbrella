<template>
  <div class="app-boot-loader" role="status" aria-live="polite" aria-label="Загрузка интерфейса">
    <div class="app-boot-loader__shell">
      <div class="app-boot-loader__mark">
        <svg
          class="app-boot-loader__shield"
          viewBox="0 0 64 64"
          fill="none"
          aria-hidden="true"
        >
          <path
            class="app-boot-loader__shield-outline"
            pathLength="1"
            d="M32 8L47 14V28C47 39.4 40.4 49.6 32 55C23.6 49.6 17 39.4 17 28V14L32 8Z"
          />
          <path
            class="app-boot-loader__shield-inner"
            d="M32 16L40 19.2V28.4C40 35.8 35.8 42.2 32 45.2C28.2 42.2 24 35.8 24 28.4V19.2L32 16Z"
          />
        </svg>
      </div>

      <div class="app-boot-loader__copy">
        <p class="app-boot-loader__eyebrow">Umbrella Console</p>
        <p class="app-boot-loader__title">Подготавливаем рабочее пространство</p>
        <p class="app-boot-loader__text">Загружаем интерфейс и синхронизируем сессию</p>
      </div>
    </div>
  </div>
</template>
