import { createApp } from 'vue'
import { registerPlugin } from './plugins'
import pinia from './plugins/pinia'
import 'primeicons/primeicons.css'
import './assets/css/app.css'

import App from './App.vue'
import { useAuthStore } from './stores/auth.store'

const app = createApp(App)

registerPlugin(app)

const authStore = useAuthStore(pinia)
authStore.refresh().catch(() => {
  // route guards handle unauthenticated state
})

app.mount('#app')
