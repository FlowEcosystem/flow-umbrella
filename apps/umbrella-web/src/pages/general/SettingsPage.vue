<script setup>
import { useCurrentUser } from '@/composables/auth/useCurrentUser'

const { user, roleLabel } = useCurrentUser()

const initials = computed(() => {
  const name = user.value?.full_name || user.value?.email || ''
  return name
    .split(/[\s@]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
})

const displayName = computed(() => user.value?.full_name || user.value?.email || 'Пользователь')
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <h1 class="page-title">Настройки</h1>
      <p class="page-subtitle">Параметры аккаунта, организации и правил доступа.</p>
    </div>

    <section class="settings-section">
      <h2 class="section-title">Аккаунт</h2>

      <Card>
        <template #content>
          <div class="profile-row">
            <div class="profile-avatar" aria-hidden="true">{{ initials || '?' }}</div>
            <div class="profile-info">
              <span class="profile-name">{{ displayName }}</span>
              <div class="profile-meta">
                <span v-if="user?.email" class="profile-email">{{ user.email }}</span>
                <span v-if="user?.email && roleLabel" class="profile-meta-sep" aria-hidden="true" />
                <span class="profile-role-badge">{{ roleLabel }}</span>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </section>

    <section class="settings-section">
      <h2 class="section-title">Организация</h2>

      <Card>
        <template #content>
          <p class="settings-placeholder">
            Параметры организации, фильтры событий и глобальные политики появятся здесь.
          </p>
        </template>
      </Card>
    </section>

    <section class="settings-section">
      <h2 class="section-title">Безопасность</h2>

      <Card>
        <template #content>
          <p class="settings-placeholder">
            Управление сессиями, двухфакторная аутентификация и аудит доступа.
          </p>
        </template>
      </Card>
    </section>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.settings-header {
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

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.profile-avatar {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  background: var(--color-accent-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-lg);
  font-weight: 600;
  letter-spacing: -0.02em;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.profile-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.profile-email {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.profile-meta-sep {
  width: 3px;
  height: 3px;
  border-radius: var(--radius-full);
  background: var(--color-border-strong);
  flex-shrink: 0;
}

.profile-role-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.settings-placeholder {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}
</style>
