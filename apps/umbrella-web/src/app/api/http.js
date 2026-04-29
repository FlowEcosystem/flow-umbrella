import axios from 'axios'
import { useSessionExpired } from '@/shared/composables/useSessionExpired'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''

let _accessToken = null

export function setAccessToken(token) {
  _accessToken = token
}

export function getAccessToken() {
  return _accessToken
}

const http = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

http.interceptors.request.use((config) => {
  if (_accessToken) config.headers.Authorization = `Bearer ${_accessToken}`
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const data   = error.response?.data
    const status = error.response?.status
    const code   = data?.error_code

    // Сессия протухла — пользователь был залогинен, но токен больше не принимается
    if (status === 401 && _accessToken) {
      const SESSION_CODES = [
        'refresh_token_revoked',
        'token_invalid',
        'token_expired',
        'refresh_invalid',
      ]
      if (!code || SESSION_CODES.includes(code)) {
        const { trigger } = useSessionExpired()
        trigger()
      }
    }

    return Promise.reject({
      error_code: code ?? 'unknown_error',
      message: data?.message ?? error.message ?? 'An error occurred',
      details: data?.details ?? {},
      status,
    })
  },
)

export default http
