const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
).replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function formatDetail(detail) {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.detail || 'Invalid value')
      .join(', ')
  }
  return ''
}

async function extractError(response) {
  try {
    const data = await response.json()
    return formatDetail(data?.detail) || `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      // Send and accept the HttpOnly session cookie.
      credentials: 'include',
    })
  } catch {
    throw new ApiError(
      'Could not reach the server. Is the backend running?',
      0,
    )
  }

  if (!response.ok) {
    throw new ApiError(await extractError(response), response.status)
  }

  return response
}

export async function requestJson(path, options) {
  const response = await request(path, options)
  if (response.status === 204) return null
  const text = await response.text()
  return text ? JSON.parse(text) : null
}

export { API_BASE_URL }
