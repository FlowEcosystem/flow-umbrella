<template>
  <aside class="w-13 bg-base-200 border-r border-base-300 flex flex-col items-center py-3 gap-2">
    <!-- Top Panel - Brand -->
    <SidebarTopPanel />
    <div class="divider my-0"></div>

    <!-- Central Panel - Buttons -->
    <SidebarCentralPanel />
    <div class="divider my-0"></div>

    <!-- Spacer -->
    <div class="flex-1"></div>

    <!-- Bottom - Settings/Logout -->
    <div class="divider my-0"></div>
    <SidebarBottomPanel />
  </aside>
</template>
