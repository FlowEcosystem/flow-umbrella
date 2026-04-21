import http from '@/app/api/http'

export const agentsApi = {
  list: ({ limit = 50, offset = 0, status, os, search, signal } = {}) =>
    http
      .get('/v1/agents', {
        signal,
        params: {
          limit,
          offset,
          status: status?.length ? status : undefined,
          os: os || undefined,
          search: search?.trim() || undefined,
        },
      })
      .then((r) => r.data),
  get: (id) => http.get(`/v1/agents/${id}`).then((r) => r.data),
  create: (payload) => http.post('/v1/agents', payload).then((r) => r.data),
  update: (id, patch) => http.patch(`/v1/agents/${id}`, patch).then((r) => r.data),
  remove: (id) => http.delete(`/v1/agents/${id}`).then(() => undefined),
  regenerateEnrollmentToken: (id) =>
    http.post(`/v1/agents/${id}/regenerate-enrollment-token`).then((r) => r.data),
}
