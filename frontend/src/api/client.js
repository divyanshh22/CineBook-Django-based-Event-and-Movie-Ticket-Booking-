import axios from 'axios'

/**
 * Axios instance shared by the whole app.
 *
 * - Base URL comes from VITE_API_BASE_URL (defaults to `/api`, proxied to
 *   the Django server by Vite in development).
 * - `withCredentials` sends the session cookie.
 * - The request interceptor attaches the CSRF token (read from the
 *   `csrftoken` cookie) to every state-changing request.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true,
  timeout: 30000,
})

const SAFE_METHODS = ['get', 'head', 'options', 'trace']

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (!SAFE_METHODS.includes(method)) {
    const csrfToken = getCookie('csrftoken')
    if (csrfToken) config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

/**
 * Normalise an error into `{ message, fieldErrors }`.
 * `fieldErrors` maps field name -> first error string (for form rendering).
 */
export function extractError(error, fallback = 'Something went wrong. Please try again.') {
  const response = error?.response
  const data = response?.data || {}

  if (response?.status === 403 && data?.detail === 'CSRF Failed: CSRF cookie not set.') {
    return { message: 'Session expired. Please refresh the page.', fieldErrors: {} }
  }

  if (response?.status === 401) {
    return { message: 'You are not authorised. Please log in again.', fieldErrors: {} }
  }

  if (typeof data === 'string') {
    return { message: data, fieldErrors: {} }
  }

  const fieldErrors = {}
  for (const [key, value] of Object.entries(data)) {
    const first = Array.isArray(value) ? value[0] : value
    if (typeof first === 'string') fieldErrors[key] = first
  }

  return {
    message: fieldErrors.detail || fallback,
    fieldErrors,
  }
}

/** Re-fetch the CSRF token cookie from the server. */
export async function fetchCsrfToken() {
  await api.get('/auth/csrf/')
}
