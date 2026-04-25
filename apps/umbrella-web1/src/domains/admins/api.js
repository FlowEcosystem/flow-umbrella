import http from '@/app/api/http'

export const adminsApi = {
  list:   (params) => http.get('/v1/admins', { params }).then(r => r.data),
  create: (data)   => http.post('/v1/admins', data).then(r => r.data),
  update: (id, data) => http.patch(`/v1/admins/${id}`, data).then(r => r.data),
  delete: (id)     => http.delete(`/v1/admins/${id}`),
}
