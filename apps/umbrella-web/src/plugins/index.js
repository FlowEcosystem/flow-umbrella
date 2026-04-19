import router from './router'
import pinia from './pinia'
import lucide from './lucide'

export function registerPlugin(app) {
  app.use(pinia)
  app.use(lucide)
  app.use(router)
}
