import router from './router'
import pinia from './pinia'
import lucide from './lucide'
import primevue from './primevue'

export function registerPlugin(app) {
  app.use(pinia)
  app.use(lucide)
  app.use(primevue)
  app.use(router)
}
