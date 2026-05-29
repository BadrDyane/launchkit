// launchkit/frontend/src/api/auth.js
import { apiJson, storeRefreshToken } from './client.js'

export async function login(email, password) {
  const data = await apiJson('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    skipOrgHeader: true,
  })
  if (data.refresh_token) storeRefreshToken(data.refresh_token)
  return data
}

export async function signup(email, password, displayName) {
  const data = await apiJson('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
    skipOrgHeader: true,
  })
  if (data.refresh_token) storeRefreshToken(data.refresh_token)
  return data
}

export async function logout(refreshToken) {
  return apiJson('/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

export async function getMe() {
  return apiJson('/auth/me', { skipOrgHeader: true })
}

export async function requestPasswordReset(email) {
  return apiJson('/user/request-password-reset', {
    method: 'POST',
    body: JSON.stringify({ email }),
    skipOrgHeader: true,
  })
}

export async function confirmPasswordReset(token, newPassword) {
  return apiJson('/user/confirm-password-reset', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
    skipOrgHeader: true,
  })
}

export async function sendVerificationEmail() {
  return apiJson('/user/send-verification-email', { method: 'POST' })
}