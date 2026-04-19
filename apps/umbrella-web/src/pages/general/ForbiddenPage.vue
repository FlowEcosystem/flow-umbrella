<script setup>
const router = useRouter()
</script>

<template>
  <UiErrorPage
    code="403"
    title="Доступ ограничен"
    description="У вашей текущей роли нет прав для просмотра этого раздела."
    variant="danger"
  >
    <template #icon>
      <ShieldAlert class="icon-lg" />
    </template>

    <template #actions>
      <Button severity="secondary" @click="router.push('/')">
        <House class="icon-sm" />
        <span>На главную</span>
      </Button>
    </template>
  </UiErrorPage>
</template>
