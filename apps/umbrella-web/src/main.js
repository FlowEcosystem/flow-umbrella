import { createApp } from 'vue'
import { registerPlugin } from './plugins'
import pinia from './plugins/pinia'

import App from './App.vue'
import { useAuthStore } from './stores/auth.store'

const app = createApp(App)

registerPlugin(app)

const authStore = useAuthStore(pinia)
await authStore.bootstrap()

app.mount('#app')
