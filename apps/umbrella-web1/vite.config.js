import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      dirs: ['src/shared/ui', 'src/app/layouts'],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: '127.0.0.1',
    port: 9080,
    strictPort: true,
    allowedHosts: ['app.umbrella.su'],
    hmr: {
      host: 'app.umbrella.su',
      protocol: 'wss',
      clientPort: 443,
    },
    proxy: {
      '/v1': {
        target: 'http://localhost:9090',
        changeOrigin: true,
      },
    },
  },
})
