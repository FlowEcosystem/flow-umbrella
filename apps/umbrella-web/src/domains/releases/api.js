import http from '@/app/api/http'

export const releasesApi = {
  list:   (platform) => http.get('/v1/admin/releases', { params: platform ? { platform } : {} }).then(r => r.data),
  remove: (id) => http.delete(`/v1/admin/releases/${id}`),
}
