import http from '@/app/api/http'

export const groupsApi = {
  list: ({ limit = 50, offset = 0 } = {}) =>
    http.get('/v1/groups', { params: { limit, offset } }).then((r) => r.data),
  get: (id) => http.get(`/v1/groups/${id}`).then((r) => r.data),
  create: (payload) => http.post('/v1/groups', payload).then((r) => r.data),
  update: (id, patch) => http.patch(`/v1/groups/${id}`, patch).then((r) => r.data),
  remove: (id) => http.delete(`/v1/groups/${id}`).then(() => undefined),
  listAgents: ({ groupId, limit = 50, offset = 0 } = {}) =>
    http.get(`/v1/groups/${groupId}/agents`, { params: { limit, offset } }).then((r) => r.data),
  addAgents: (groupId, agentIds) =>
    http.post(`/v1/groups/${groupId}/agents`, { agent_ids: agentIds }).then((r) => r.data),
  removeAgent: (groupId, agentId) => http.delete(`/v1/groups/${groupId}/agents/${agentId}`).then(() => undefined),
}
