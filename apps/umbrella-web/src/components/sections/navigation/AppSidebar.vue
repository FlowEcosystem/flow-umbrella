<script setup>
defineProps({
  collapsed: { type: Boolean, default: false },
  mobile: { type: Boolean, default: false },
  open: { type: Boolean, default: true },
})

defineEmits(['toggle'])
</script>

<template>
  <aside
    class="app-sidebar"
    :class="{
      'app-sidebar--collapsed': collapsed,
      'app-sidebar--mobile': mobile,
      'app-sidebar--open': open,
    }"
  >
    <SidebarTopPanel :collapsed="collapsed" :mobile="mobile" @toggle="$emit('toggle')" />
    <SidebarCentralPanel :collapsed="collapsed" />
    <SidebarBottomPanel :collapsed="collapsed" />
  </aside>
</template>
