import http from '@/app/api/http'

export const groupsApi = {
  list:         (params)          => http.get('/v1/groups', { params }).then(r => r.data),
  get:          (id)              => http.get(`/v1/groups/${id}`).then(r => r.data),
  create:       (data)            => http.post('/v1/groups', data).then(r => r.data),
  update:       (id, data)        => http.patch(`/v1/groups/${id}`, data).then(r => r.data),
  delete:       (id)              => http.delete(`/v1/groups/${id}`),
  listAgents:   (id)              => http.get(`/v1/groups/${id}/agents`, { params: { limit: 200 } }).then(r => r.data),
  addAgents:    (id, agent_ids)   => http.post(`/v1/groups/${id}/agents`, { agent_ids }).then(r => r.data),
  removeAgent:  (id, agent_id)    => http.delete(`/v1/groups/${id}/agents/${agent_id}`),
  listPolicies: (id)              => http.get(`/v1/groups/${id}/policies`).then(r => r.data),
}
