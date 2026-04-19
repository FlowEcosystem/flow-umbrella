<template>
  <footer
    class="mt-auto border-t border-base-200 bg-base-100/70 backdrop-blur px-4 py-3 text-sm text-base-content/60"
  >
    <div class="flex items-center justify-between gap-4">
      <!-- left -->
      <div class="flex items-center gap-2">
        <span class="font-medium text-base-content/80">Flow</span>
        <span class="opacity-40">•</span>
        <span>© {{ new Date().getFullYear() }}</span>
      </div>

      <!-- right -->
      <div class="flex items-center gap-3">
        <span class="hidden sm:inline-flex items-center gap-1">
          <span class="opacity-60">v{{ appVersion }}</span>
          <span class="opacity-40">•</span>
          <span class="font-mono text-xs opacity-70">{{ shortHash }}</span>
        </span>

        <a class="hover:text-base-content transition-colors" href="#">Поддержка</a>
        <a class="hidden sm:inline hover:text-base-content transition-colors" href="#">Политика</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
const appVersion = import.meta.env.VITE_APP_VERSION ?? '0.0.0'
const buildHash = import.meta.env.VITE_BUILD_HASH ?? 'dev'
const shortHash = buildHash.slice(0, 7)
</script>
