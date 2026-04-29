import http from '@/app/api/http'

export const auditApi = {
  list: (params) => http.get('/v1/audit-log', { params }).then(r => r.data),
}
