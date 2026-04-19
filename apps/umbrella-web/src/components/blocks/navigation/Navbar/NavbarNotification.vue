<script setup>
const props = defineProps({
  nots: {
    type: Array,
    required: true,
  },
  unreadCount: {
    type: Number,
    required: true,
  },
  actions: {
    type: Object,
    required: true,
  },
})

const open = ref(false)

function toggleDropdown() {
  open.value = !open.value
}

function markRead(notification) {
  props.actions.read(notification.id)
}
</script>

<template>
  <div class="dropdown dropdown-end" :class="{ 'dropdown-open': open }">
    <button
      class="btn btn-ghost btn-square rounded-2xl relative"
      aria-label="Уведомления"
      @click="toggleDropdown"
    >
      <Bell class="size-5" />
      <span v-if="unreadCount > 0" class="badge badge-error badge-sm absolute -top-1 -right-1 px-2">
        {{ unreadCount }}
      </span>
    </button>

    <div
      tabindex="0"
      class="dropdown-content z-50 mt-3 w-[360px] max-w-[calc(100vw-2rem)] rounded-2xl border border-base-300 bg-base-100 shadow-sm"
    >
      <div class="p-4 pb-3 border-b border-base-300">
        <div class="flex justify-between gap-3 items-center">
          <div class="min-w-0">
            <div class="font-semibold text-base">Уведомления</div>
            <div class="text-xs text-base-content/60">
              <span v-if="unreadCount > 0">Непрочитанных: {{ unreadCount }}</span>
              <span v-else>Всё прочитано</span>
            </div>
          </div>

          <div class="flex gap-2">
            <button
              class="btn btn-error btn-soft btn-xs rounded-xl"
              :disabled="nots.length === 0"
              @click="actions.clear()"
            >
              Очистить
            </button>
            <button
              class="btn btn-primary btn-soft btn-xs rounded-xl"
              :disabled="unreadCount === 0"
              @click="actions.readAll()"
            >
              Прочитать всё
            </button>
          </div>
        </div>
      </div>

      <div class="max-h-105 overflow-auto p-2">
        <div v-if="nots.length === 0" class="p-6 text-center">
          <div class="text-sm font-medium">Пока тихо</div>
          <div class="text-xs text-base-content/60 mt-1">Здесь будут появляться новые события.</div>
        </div>

        <ul v-else class="space-y-2">
          <li v-for="n in nots" :key="n.id" class="group">
            <button
              class="w-full text-left rounded-2xl border border-base-200 p-3 hover:border-base-300 hover:bg-base-200/40 transition focus:outline-none focus-visible:ring focus-visible:ring-primary/30"
              @click="markRead(n)"
            >
              <div class="flex items-start gap-3">
                <div class="pt-1">
                  <span
                    class="block size-2 rounded-full"
                    :class="n.read ? 'bg-base-300' : 'bg-primary'"
                  />
                </div>

                <div class="min-w-0 flex-1">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div
                        class="font-medium truncate"
                        :class="n.read ? 'text-base-content/80' : 'text-base-content'"
                      >
                        {{ n.title }}
                      </div>
                      <div class="text-xs text-base-content/60 truncate mt-0.5">
                        {{ n.subtitle }}
                      </div>
                    </div>
                  </div>

                  <div class="mt-2 flex items-center gap-2">
                    <span
                      v-if="!n.read"
                      class="badge badge-primary badge-outline badge-xs rounded-lg"
                    >
                      Новое
                    </span>
                    <span
                      class="text-[11px] text-base-content/50 opacity-0 group-hover:opacity-100 transition"
                    >
                      Нажми, чтобы отметить прочитанным
                    </span>
                  </div>
                </div>
              </div>
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
