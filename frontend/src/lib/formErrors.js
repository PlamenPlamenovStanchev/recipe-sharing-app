import { ApiError } from './api.js'

export function getRequestErrorMessage(error) {
  if (error instanceof ApiError) {
    const validationErrors = error.data?.errors
    if (validationErrors) {
      const messages = Object.values(validationErrors).flat().filter(Boolean)
      if (messages.length > 0) return messages.join(' ')
    }
    return error.message
  }

  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}
