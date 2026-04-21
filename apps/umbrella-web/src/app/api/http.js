import axios from 'axios'

const baseURL = (import.meta.env.VITE_API_BASE_URL ?? 'https://api.umbrella.su').replace(/\/$/, '')

let _accessToken = null

export function setAccessToken(token) {
  _accessToken = token
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
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const data = error.response?.data
    return Promise.reject({
      error_code: data?.error_code ?? 'unknown_error',
      message: data?.message ?? error.message ?? 'An error occurred',
      details: data?.details ?? {},
      status: error.response?.status,
    })
  },
)

export default http
