import { createApp } from 'vue'
import { registerPlugin } from './app/plugins'
import pinia from './app/plugins/pinia'
import 'primeicons/primeicons.css'
import './assets/css/app.css'

import App from './App.vue'
import { useAuthStore } from './domains/auth/store'

const app = createApp(App)

registerPlugin(app)

const authStore = useAuthStore(pinia)
authStore.refresh().catch(() => {
  // route guards handle unauthenticated state
})

app.mount('#app')
