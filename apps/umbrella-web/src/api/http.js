const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')

function buildUrl(path) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export class ApiError extends Error {
  constructor(message, options = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status ?? 500
    this.payload = options.payload ?? null
  }
}

export async function apiRequest(path, options = {}) {
  const { method = 'GET', body, headers = {}, credentials = 'include', signal } = options

  const config = {
    method,
    credentials,
    signal,
    headers: {
      Accept: 'application/json',
      ...headers,
    },
  }

  if (body !== undefined) {
    if (body instanceof FormData) {
      config.body = body
    } else {
      config.body = JSON.stringify(body)
      config.headers['Content-Type'] = 'application/json'
    }
  }

  const response = await fetch(buildUrl(path), config)

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') ?? ''
  const payload = contentType.includes('application/json')
    ? await response.json().catch(() => null)
    : await response.text().catch(() => '')

  if (!response.ok) {
    throw new ApiError(payload?.message || `API request failed with status ${response.status}`, {
      status: response.status,
      payload,
    })
  }

  return payload
}

export function getApiBaseUrl() {
  return API_BASE_URL
}
