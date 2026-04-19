<template>
  <div class="flex min-h-screen bg-base-100">
    <!-- SIDEBAR -->
    <AppSidebar />

    <!-- PAGE CONTENT / NAVBAR -->
    <div class="flex-1 flex flex-col">
      <AppNavbar />

      <!-- PAGE CONTENT -->
      <main class="flex-1 p-4">
        <router-view />
      </main>

      <!-- FOOTER -->
      <AppFooter />
    </div>
  </div>
</template>
