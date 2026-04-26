import http from '@/app/api/http'

export const agentsApi = {
  list:            (params) => http.get('/v1/agents', { params }).then(r => r.data),
  get:             (id)     => http.get(`/v1/agents/${id}`).then(r => r.data),
  create:          (data)   => http.post('/v1/agents', data).then(r => r.data),
  update:          (id, data) => http.patch(`/v1/agents/${id}`, data).then(r => r.data),
  delete:          (id)     => http.delete(`/v1/agents/${id}`),
  regenerateToken: (id)     => http.post(`/v1/agents/${id}/regenerate-enrollment-token`).then(r => r.data),
  listGroups:      (id)     => http.get(`/v1/agents/${id}/groups`).then(r => r.data),
  listPolicies:    (id)     => http.get(`/v1/agents/${id}/policies`).then(r => r.data),
  listCommands:             (id)     => http.get(`/v1/agents/${id}/commands`).then(r => r.data),
  issueCommand:             (id, data) => http.post(`/v1/agents/${id}/commands`, data).then(r => r.data),
  generateDecommissionToken:(id)     => http.post(`/v1/agents/${id}/decommission-token`).then(r => r.data),
  getMetrics:               (id, limit = 60) => http.get(`/v1/agents/${id}/metrics`, { params: { limit } }).then(r => r.data),
}
