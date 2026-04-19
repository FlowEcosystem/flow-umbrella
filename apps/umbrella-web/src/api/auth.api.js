import http from './http'

export const authApi = {
  login: (credentials) => http.post('/v1/auth/login', credentials).then((r) => r.data),
  logout: () => http.post('/v1/auth/logout').then((r) => r.data),
  me: () => http.get('/v1/auth/me').then((r) => r.data),
  refresh: () => http.post('/v1/auth/refresh').then((r) => r.data),
}
