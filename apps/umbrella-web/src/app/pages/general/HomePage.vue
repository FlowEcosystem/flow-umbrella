<script setup>
import { useCurrentUser } from '@/domains/auth/useCurrentUser'

const { user } = useCurrentUser()

const greeting = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'Оператор'
  const h = new Date().getHours()
  if (h < 6) return `Доброй ночи, ${name}`
  if (h < 12) return `Доброе утро, ${name}`
  if (h < 18) return `Добрый день, ${name}`
  return `Добрый вечер, ${name}`
})

const stats = [
  { key: 'agents',    label: 'Агенты',     icon: 'Monitor',      value: '—', hint: 'Подключённые устройства' },
  { key: 'policies',  label: 'Политики',   icon: 'ShieldCheck',  value: '—', hint: 'Активных правил' },
  { key: 'groups',    label: 'Группы',     icon: 'Users',        value: '—', hint: 'Групп устройств' },
  { key: 'incidents', label: 'Инциденты',  icon: 'AlertCircle',  value: '—', hint: 'За последние 24 ч' },
]
</script>

<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h1 class="page-title">{{ greeting }}</h1>
      <p class="page-subtitle">
        Панель управления агентами, политиками и телеметрией.
      </p>
    </div>

    <div class="stat-grid">
      <div v-for="stat in stats" :key="stat.key" class="stat-card">
        <div class="stat-icon">
          <component :is="stat.icon" class="icon-md" />
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
        <span class="stat-hint">{{ stat.hint }}</span>
      </div>
    </div>

    <Card class="overview-card">
      <template #content>
        <div class="overview-content">
          <div class="overview-mark">
            <Shield class="icon-xl" />
          </div>
          <div class="overview-copy">
            <p class="overview-title">Система готова к работе</p>
            <p class="overview-text">
              Каркас развёрнут. Здесь появятся агенты, политики и телеметрия — как только
              соответствующие разделы будут подключены.
            </p>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.dashboard-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.page-title {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 400;
  line-height: 1.08;
  letter-spacing: -0.025em;
}

.page-subtitle {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: border-color 0.15s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
}

.stat-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  background: var(--color-surface-subtle);
  border-radius: var(--radius-md);
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.stat-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: auto;
}

.overview-card :deep(.p-card-body) {
  padding: 20px 24px;
}

.overview-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.overview-mark {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  background: var(--color-accent-subtle);
  border-radius: var(--radius-lg);
}

.overview-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overview-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

.overview-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
}

@media (max-width: 1023px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .page-title {
    font-size: var(--text-xl);
  }

  .overview-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
}
</style>
