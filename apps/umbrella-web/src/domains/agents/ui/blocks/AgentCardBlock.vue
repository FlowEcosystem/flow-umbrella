<script setup>
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import { CheckCircle2, Ellipsis, KeyRound, Pencil, XCircle } from 'lucide-vue-next'

import {
  formatAgentLastSeen,
  formatEnrolledAt,
  getAgentOsLabel,
  getAgentStatusClass,
  getAgentStatusLabel,
} from '@/domains/agents/agents.utils'

defineProps({
  agent: {
    type: Object,
    required: true,
  },
  canWriteAgents: {
    type: Boolean,
    default: false,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
  busyLabel: {
    type: String,
    default: '',
  },
  pendingAction: {
    type: String,
    default: null,
  },
  onEdit: {
    type: Function,
    required: true,
  },
  onToken: {
    type: Function,
    required: true,
  },
  onMenu: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <article class="agent-card" :class="`agent-card--${agent.status}`">
    <div v-if="isBusy" class="agent-card__busy">
      <ProgressSpinner class="agent-card__busy-spinner" stroke-width="5" fill="transparent" animation-duration=".8s" />
      <span class="agent-card__busy-label">{{ busyLabel }}</span>
    </div>

    <div class="agent-card__header">
      <div class="primary-cell">
        <span class="primary-cell__title">{{ agent.hostname }}</span>
        <span class="primary-cell__hint">{{ agent.notes || 'Без заметок' }}</span>
      </div>
      <span class="status-badge" :class="getAgentStatusClass(agent.status)">
        {{ getAgentStatusLabel(agent.status) }}
      </span>
    </div>

    <div class="agent-card__meta-grid">
      <div class="stacked-meta">
        <span class="meta-label">OS</span>
        <span>{{ getAgentOsLabel(agent.os) }}</span>
        <span class="muted-text">{{ agent.os_version || 'Версия не указана' }}</span>
      </div>

      <div class="stacked-meta">
        <span class="meta-label">Связь</span>
        <span :class="{ 'muted-text': formatAgentLastSeen(agent.last_seen_at).muted }">
          {{ formatAgentLastSeen(agent.last_seen_at).text }}
        </span>
        <span class="muted-text">{{ agent.ip_address || 'IP неизвестен' }}</span>
      </div>

      <div class="stacked-meta">
        <span class="meta-label">Enrollment</span>
        <span>{{ formatEnrolledAt(agent.enrolled_at) }}</span>
        <span class="muted-text">{{ agent.agent_version || 'Версия агента неизвестна' }}</span>
      </div>

      <div class="stacked-meta">
        <span class="meta-label">Состояние</span>
        <div class="agent-presence" :class="{ 'is-muted': agent.status !== 'active' }">
          <CheckCircle2 v-if="agent.status === 'active'" :size="16" />
          <XCircle v-else :size="16" />
          <span>{{ agent.status === 'active' ? 'На связи' : 'Требует внимания' }}</span>
        </div>
      </div>
    </div>

    <div v-if="canWriteAgents" class="agent-card__actions">
      <div class="agent-card__actions-main">
        <div class="agent-segmented">
          <Button
            text
            class="agent-segmented__btn"
            aria-label="Редактировать агента"
            :loading="pendingAction === 'edit'"
            :disabled="isBusy"
            @click="onEdit(agent)"
          >
            <Pencil :size="15" />
            <span>Изменить</span>
          </Button>
          <Button
            text
            class="agent-segmented__btn"
            :class="agent.enrolled_at ? 'agent-segmented__btn--token-refresh' : 'agent-segmented__btn--token-create'"
            aria-label="Сгенерировать enrollment token"
            :loading="pendingAction === 'token'"
            :disabled="isBusy"
            @click="onToken(agent)"
          >
            <KeyRound :size="15" />
            <span>{{ agent.enrolled_at ? 'Перевыпустить токен' : 'Токен' }}</span>
          </Button>
        </div>
      </div>
      <Button
        text
        class="agent-card__menu-trigger"
        aria-label="Дополнительные действия"
        :disabled="isBusy"
        @click="onMenu($event, agent)"
      >
        <Ellipsis :size="16" />
        <span>Ещё</span>
      </Button>
    </div>
  </article>
</template>
