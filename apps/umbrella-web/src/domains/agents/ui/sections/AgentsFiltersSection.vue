<script setup>
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Select from 'primevue/select'
import { Search } from 'lucide-vue-next'

defineProps({
  containerRef: {
    type: null,
    default: null,
  },
  filterState: {
    type: Object,
    required: true,
  },
  statusOptions: {
    type: Array,
    required: true,
  },
  osOptions: {
    type: Array,
    required: true,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  onResetFilters: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <section :ref="containerRef" class="filters-card">
    <div class="filter-grid">
      <div class="field field--search">
        <label class="field-label" for="agents-search">Поиск</label>
        <div class="search-field">
          <Search :size="16" class="search-field__icon" />
          <InputText id="agents-search" v-model="filterState.search" placeholder="Hostname" fluid />
        </div>
      </div>

      <div class="field">
        <label class="field-label" for="agents-status">Статус</label>
        <MultiSelect
          id="agents-status"
          v-model="filterState.status"
          :options="statusOptions"
          option-label="label"
          option-value="value"
          placeholder="Все статусы"
          display="chip"
          fluid
        />
      </div>

      <div class="field">
        <label class="field-label" for="agents-os">OS</label>
        <Select
          id="agents-os"
          v-model="filterState.os"
          :options="osOptions"
          option-label="label"
          option-value="value"
          placeholder="Все ОС"
          showClear
          fluid
        />
      </div>
    </div>

    <div class="filter-actions">
      <span class="filter-actions__hint">
        {{ isLoading ? 'Обновляем список...' : 'Фильтры применяются автоматически' }}
      </span>
      <Button label="Сбросить" severity="secondary" outlined @click="onResetFilters" />
    </div>
  </section>
</template>
