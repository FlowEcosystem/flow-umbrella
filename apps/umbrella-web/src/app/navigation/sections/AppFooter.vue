<script setup>
const appVersion = import.meta.env.VITE_APP_VERSION ?? '1.0.0'

const now = ref(new Date())
let timer

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onBeforeUnmount(() => clearInterval(timer))

const dateTimeStr = computed(() =>
  now.value.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }),
)
</script>

<template>
  <footer class="app-footer">
    <div class="footer-brand">
      <Shield class="icon-sm footer-brand-icon" aria-hidden="true" />
      <span class="footer-brand-name">Umbrella</span>
      <span class="footer-sep" aria-hidden="true" />
      <span class="footer-brand-desc">Консоль управления</span>
    </div>

    <div class="footer-meta">
      <time class="footer-time" :datetime="now.toISOString()">{{ dateTimeStr }}</time>
      <span class="footer-dot" aria-hidden="true" />
      <span class="footer-version">v{{ appVersion }}</span>
      <span class="footer-dot" aria-hidden="true" />
      <span class="footer-status" aria-label="Статус системы: активна">
        <span class="footer-status-pulse" aria-hidden="true" />
        Активна
      </span>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  flex-shrink: 0;
  height: 44px;
  padding: 0 var(--layout-content-padding-x);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.footer-brand,
.footer-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-brand-icon {
  color: var(--color-accent);
  opacity: 0.7;
}

.footer-brand-name {
  color: var(--color-text-secondary);
  font-weight: 600;
  letter-spacing: -0.01em;
}

.footer-sep {
  width: 1px;
  height: 12px;
  background: var(--color-border-strong);
  flex-shrink: 0;
}

.footer-brand-desc {
  color: var(--color-text-muted);
}

.footer-dot {
  width: 3px;
  height: 3px;
  border-radius: var(--radius-full);
  background: var(--color-border-strong);
  flex-shrink: 0;
}

.footer-time {
  color: var(--color-text-muted);
}

.footer-version {
  color: var(--color-text-muted);
}

.footer-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-success);
}

.footer-status-pulse {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-success);
  animation: status-pulse 2.8s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 1023px) {
  .app-footer {
    padding: 0 20px;
  }
}

@media (max-width: 767px) {
  .app-footer {
    height: auto;
    padding: 10px 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .footer-brand-desc,
  .footer-time {
    display: none;
  }
}
</style>
