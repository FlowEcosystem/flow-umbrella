<script setup>
const props = defineProps({
  to: {
    type: String,
    required: true,
  },
  tooltip: {
    type: String,
    default: '',
  },
  exact: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()

const isActive = computed(() => {
  if (props.exact) {
    return route.path === props.to
  }
  return route.path.startsWith(props.to)
})

function navigate() {
  if (route.path !== props.to) {
    router.push(props.to)
  }
}
</script>

<template>
  <div class="tooltip tooltip-right" :data-tip="tooltip">
    <button
      class="btn btn-outline btn-ghost btn-circle border-0 transition-all duration-600"
      :class="{
        'btn-primary': isActive,
      }"
      @click="navigate"
    >
      <slot />
    </button>
  </div>
</template>
