<script setup>
import { ChevronDown } from 'lucide-vue-next'

import AgentCardBlock from './AgentCardBlock.vue'

defineProps({
  group: {
    type: Object,
    required: true,
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
  canWriteAgents: {
    type: Boolean,
    default: false,
  },
  setGroupRef: {
    type: Function,
    required: true,
  },
  onToggle: {
    type: Function,
    required: true,
  },
  isAgentBusy: {
    type: Function,
    required: true,
  },
  getPendingAgentActionLabel: {
    type: Function,
    required: true,
  },
  getPendingAgentAction: {
    type: Function,
    required: true,
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
  <section :ref="(el) => setGroupRef(group.key, el)" class="agent-group" :class="`agent-group--${group.key}`">
    <button type="button" class="agent-group__header" @click="onToggle(group.key)">
      <div class="agent-group__title-row">
        <span class="agent-group__title">{{ group.label }}</span>
        <span class="agent-group__count">{{ group.items.length }}</span>
      </div>
      <div class="agent-group__header-end">
        <div class="agent-group__rule" :class="`agent-group__rule--${group.key}`" />
        <ChevronDown :size="16" class="agent-group__chevron" :class="{ 'is-collapsed': collapsed }" />
      </div>
    </button>

    <TransitionGroup v-show="!collapsed" name="agent-cards" tag="div" class="cards-grid">
      <AgentCardBlock
        v-for="agent in group.items"
        :key="agent.id"
        :agent="agent"
        :can-write-agents="canWriteAgents"
        :is-busy="isAgentBusy(agent.id)"
        :busy-label="getPendingAgentActionLabel(agent.id)"
        :pending-action="getPendingAgentAction(agent.id)"
        :on-edit="onEdit"
        :on-token="onToken"
        :on-menu="onMenu"
      />
    </TransitionGroup>
  </section>
</template>
