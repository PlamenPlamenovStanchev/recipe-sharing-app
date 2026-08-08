import { env } from '../config/env.js'

export class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export async function apiRequest(path, options = {}) {
  const { accessToken, body, headers = {}, ...requestOptions } = options
  const isFormData = body instanceof FormData
  const requestHeaders = new Headers(headers)

  if (body !== undefined && !isFormData && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json')
  }
  if (accessToken && !requestHeaders.has('Authorization')) {
    requestHeaders.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(
    `${env.apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`,
    {
      ...requestOptions,
      headers: requestHeaders,
      body: body === undefined || isFormData ? body : JSON.stringify(body),
    },
  )

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    throw new ApiError(data?.message || 'The request could not be completed.', {
      status: response.status,
      data,
    })
  }

  return data
}

export const api = {
  get: (path, options) => apiRequest(path, { ...options, method: 'GET' }),
  post: (path, body, options) =>
    apiRequest(path, { ...options, method: 'POST', body }),
  put: (path, body, options) =>
    apiRequest(path, { ...options, method: 'PUT', body }),
  delete: (path, options) =>
    apiRequest(path, { ...options, method: 'DELETE' }),
}
