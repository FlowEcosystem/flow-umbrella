import { apiRequest } from '@/api/http'

export const notificationsApi = {
  fetchLatest() {
    return apiRequest('/notifications')
  },

  remove(id) {
    return apiRequest(`/notifications/${id}`, {
      method: 'DELETE',
    })
  },

  markRead(id) {
    return apiRequest(`/notifications/${id}/read`, {
      method: 'POST',
    })
  },

  markAllRead() {
    return apiRequest('/notifications/read-all', {
      method: 'POST',
    })
  },

  clear() {
    return apiRequest('/notifications', {
      method: 'DELETE',
    })
  },
}
