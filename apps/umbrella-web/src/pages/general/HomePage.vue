<script setup>
import { getRoleLabel, ROLES } from '@/config/rbac'
import { useNavigation } from '@/composables/navigation/useNavigation'

const authStore = useAuthStore()
const { quickActions } = useNavigation()

const roleDescriptions = {
  [ROLES.STUDENT]:
    'Личный учебный кабинет: расписание, домашние задания, оценки, методпакеты и персональная статистика.',
  [ROLES.TEACHER]:
    'Рабочее место преподавателя: расписание, закрепленные группы, выдача и проверка домашних заданий.',
  [ROLES.MANAGER]:
    'Операционный контур менеджера: расписание, сущности колледжа, отчеты, impersonation и управление филиалом.',
  [ROLES.DIRECTOR]:
    'Полный административный контур: управление доступами, аудитом, отчетностью и критичными действиями.',
}

const actionDescriptions = {
  '/schedule': 'Пары, аудитории, преподаватели и изменения учебной сетки.',
  '/homework': 'Постановка, сдача, проверка и возврат домашних заданий.',
  '/grades': 'Оценки по периодам, ведомости и динамика успеваемости.',
  '/materials': 'Методические материалы и библиотека дисциплин.',
  '/students': 'Карточки студентов и контроль контингента.',
  '/groups': 'Группы, состав, статистика и кураторство.',
  '/disciplines': 'Справочник дисциплин и учебной структуры.',
  '/reports': 'Отчеты, выгрузки и аналитика по филиалу.',
  '/administration': 'Роли, доступы, impersonation и аудит.',
}

const architectureHighlights = [
  'Единая матрица ролей и прав доступа.',
  'Role-based навигация без статичных админских секций.',
  'API-слой вместо моковых данных.',
  'Доменная разбивка по модулям колледжа.',
]

const primaryActions = computed(() =>
  quickActions.value.slice(0, authStore.hasRole([ROLES.MANAGER, ROLES.DIRECTOR]) ? 8 : 6),
)
const currentRoleLabel = computed(() => getRoleLabel(authStore.role))
const currentRoleDescription = computed(
  () => roleDescriptions[authStore.role] ?? 'Войдите в систему, чтобы открыть кабинет по своей роли.',
)
</script>

<template>
  <section class="mx-auto max-w-[1700px] space-y-6">
    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div class="max-w-3xl">
          <div class="badge badge-outline rounded-xl px-3 py-3">
            {{ authStore.isAuthenticated ? currentRoleLabel : 'Гостевой режим' }}
          </div>
          <h1 class="mt-4 text-3xl font-semibold tracking-tight">Flow для колледжа</h1>
          <p class="mt-3 text-sm leading-6 text-base-content/70">
            {{ currentRoleDescription }}
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-2 xl:w-[32rem]">
          <article
            v-for="highlight in architectureHighlights"
            :key="highlight"
            class="rounded-2xl border border-base-300 bg-base-200/40 p-4 text-sm"
          >
            {{ highlight }}
          </article>
        </div>
      </div>
    </div>

    <div class="rounded-3xl border border-base-300 bg-base-100 p-6 shadow-sm">
      <div>
        <h2 class="text-xl font-semibold tracking-tight">Быстрый доступ</h2>
        <p class="mt-1 text-sm text-base-content/60">
          Доступные модули фильтруются по роли. Общей панели для всех пользователей больше нет.
        </p>
      </div>

      <div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <RouterLink
          v-for="action in primaryActions"
          :key="action.to"
          :to="action.to"
          class="group rounded-2xl border border-base-300 bg-base-100 p-4 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:bg-base-200/50 hover:shadow-sm"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="text-sm font-semibold">{{ action.label }}</div>
              <div class="mt-1 text-xs text-base-content/60">
                {{ actionDescriptions[action.to] }}
              </div>
            </div>

            <div
              class="flex size-10 shrink-0 items-center justify-center rounded-xl bg-base-200 transition group-hover:bg-primary/10"
            >
              <component :is="action.icon" class="size-4 transition group-hover:text-primary" />
            </div>
          </div>
        </RouterLink>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-3">
      <article class="rounded-3xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div class="text-sm font-semibold">Student MVP</div>
        <p class="mt-2 text-sm text-base-content/70">
          Расписание, ДЗ, загрузка решений, оценки, методпакеты и личная статистика.
        </p>
      </article>

      <article class="rounded-3xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div class="text-sm font-semibold">Teacher MVP</div>
        <p class="mt-2 text-sm text-base-content/70">
          Закрепленные группы, постановка домашних заданий, проверка работ и статистика группы.
        </p>
      </article>

      <article class="rounded-3xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div class="text-sm font-semibold">Manager / Director</div>
        <p class="mt-2 text-sm text-base-content/70">
          Расписание, сущности колледжа, доступы, аудит и аналитика по филиалу.
        </p>
      </article>
    </div>
  </section>
</template>
