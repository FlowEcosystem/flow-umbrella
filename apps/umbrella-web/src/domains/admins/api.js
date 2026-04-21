import http from '@/app/api/http'

export const adminsApi = {
  list: ({ limit = 50, offset = 0 } = {}) =>
    http.get('/v1/admins', { params: { limit, offset } }).then((r) => r.data),
  get: (id) => http.get(`/v1/admins/${id}`).then((r) => r.data),
  create: (payload) => http.post('/v1/admins', payload).then((r) => r.data),
  update: (id, patch) => http.patch(`/v1/admins/${id}`, patch).then((r) => r.data),
  remove: (id) => http.delete(`/v1/admins/${id}`).then(() => undefined),
}
