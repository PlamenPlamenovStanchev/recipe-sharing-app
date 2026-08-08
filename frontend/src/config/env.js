const defaultApiBaseUrl = 'http://localhost:5000'

export const env = Object.freeze({
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl).replace(
    /\/$/,
    '',
  ),
})
