<script setup>
defineProps({
  code: { type: [String, Number], required: true },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  variant: { type: String, default: 'default' },
})
</script>

<template>
  <div class="error-page">
    <div class="error-shell">
      <div class="error-brand" aria-hidden="true">
        <Shield class="icon-sm error-brand-icon" />
        <span class="error-brand-name">Umbrella</span>
      </div>

      <div class="error-body">
        <div class="error-icon-wrap" :class="`error-icon-wrap--${variant}`">
          <slot name="icon" />
        </div>

        <h1 class="error-code" :class="`error-code--${variant}`">{{ code }}</h1>

        <div class="error-text">
          <h2 class="error-title">{{ title }}</h2>
          <p v-if="description" class="error-description">{{ description }}</p>
        </div>

        <div class="error-actions">
          <slot name="actions" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: var(--color-bg);
}

.error-shell {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}

.error-brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
}

.error-brand-icon {
  color: var(--color-accent);
  opacity: 0.6;
}

.error-brand-name {
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: -0.01em;
}

.error-body {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.error-icon-wrap {
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  background: var(--color-surface-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.error-icon-wrap--danger {
  color: var(--color-danger);
  background: var(--color-danger-subtle);
  border-color: var(--color-danger-border);
}

.error-code {
  font-family: var(--font-serif);
  font-size: 96px;
  font-weight: 400;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--color-text);
  margin: -8px 0;
}

.error-code--danger {
  color: var(--color-danger);
  opacity: 0.85;
}

.error-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
}

.error-description {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
}

.error-actions {
  display: flex;
  justify-content: center;
}

@media (max-width: 767px) {
  .error-page {
    padding: 24px 16px;
    align-items: flex-start;
    padding-top: 80px;
  }

  .error-code {
    font-size: 72px;
  }
}
</style>
