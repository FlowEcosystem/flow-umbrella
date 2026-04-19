<script setup>
const router = useRouter()
</script>

<template>
  <UiErrorPage
    code="404"
    title="Страница не найдена"
    description="Запрошенный адрес недоступен или был перемещён."
  >
    <template #icon>
      <MapPinned class="icon-lg" />
    </template>

    <template #actions>
      <Button severity="secondary" @click="router.push('/')">
        <House class="icon-sm" />
        <span>На главную</span>
      </Button>
    </template>
  </UiErrorPage>
</template>
