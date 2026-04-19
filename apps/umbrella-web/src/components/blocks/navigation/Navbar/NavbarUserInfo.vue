<script setup>
const props = defineProps({
  userFullName: {
    type: String,
    default: 'Гость',
  },
  userPosition: {
    type: String,
    default: 'Нет активной сессии',
  },
  userAvatarUrl: {
    type: String,
    default: '',
  },
})

const initials = computed(() =>
  props.userFullName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase(),
)
</script>

<template>
  <div class="flex items-center gap-3 px-2">
    <div class="avatar">
      <div
        class="flex w-12 items-center justify-center rounded-xl bg-primary/10 text-sm font-semibold text-primary"
      >
        <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="Аватар" />
        <span v-else>{{ initials || 'FL' }}</span>
      </div>
    </div>

    <div class="hidden sm:flex flex-col leading-tight cursor-default">
      <span class="text-sm font-medium">{{ userFullName }}</span>
      <span class="text-xs opacity-60">{{ userPosition }}</span>
    </div>
  </div>
</template>
