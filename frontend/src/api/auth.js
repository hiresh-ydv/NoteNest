import { requestJson } from './client.js'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export function registerUser(email, password) {
  return requestJson('/auth/register', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email, password }),
  })
}

export function loginUser(email, password) {
  return requestJson('/auth/login', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ email, password }),
  })
}

export function logoutUser() {
  return requestJson('/auth/logout', { method: 'POST' })
}

export function getMe() {
  return requestJson('/auth/me')
}

export function verifyEmail(code) {
  return requestJson('/auth/verify-email', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ code }),
  })
}

export function resendOtp() {
  return requestJson('/auth/resend-otp', { method: 'POST' })
}
