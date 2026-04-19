import { apiRequest } from '@/api/http'

export const sessionApi = {
  fetchCurrentSession() {
    return apiRequest('/session')
  },

  logout() {
    return apiRequest('/auth/logout', {
      method: 'POST',
    })
  },
}
