import http from '@/app/api/http'

export const policiesApi = {
  list:           (params)     => http.get('/v1/policies', { params }).then(r => r.data),
  get:            (id)         => http.get(`/v1/policies/${id}`).then(r => r.data),
  create:         (data)       => http.post('/v1/policies', data).then(r => r.data),
  update:         (id, data)   => http.patch(`/v1/policies/${id}`, data).then(r => r.data),
  delete:         (id)         => http.delete(`/v1/policies/${id}`),
  getAssignments: (id)         => http.get(`/v1/policies/${id}/assignments`).then(r => r.data),
  assign:         (id, data)   => http.post(`/v1/policies/${id}/assign`, data),
}

export const servicesApi = {
  list:   (params) => http.get('/v1/services', { params }).then(r => r.data),
  get:    (id)     => http.get(`/v1/services/${id}`).then(r => r.data),
  create: (data)   => http.post('/v1/services', data).then(r => r.data),
  update: (id, data) => http.patch(`/v1/services/${id}`, data).then(r => r.data),
  delete: (id)     => http.delete(`/v1/services/${id}`),
}
