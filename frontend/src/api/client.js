// launchkit/frontend/src/api/client.js
const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

let _accessToken = null
let _refreshPromise = null

export function setAccessToken(token) {
  _accessToken = token
}

export function getAccessToken() {
  return _accessToken
}

async function refreshAccessToken() {
  // Only one refresh at a time — deduplicate concurrent requests
  if (_refreshPromise) return _refreshPromise

  _refreshPromise = fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: getStoredRefreshToken() }),
  })
    .then(async (res) => {
      if (!res.ok) throw new Error('Refresh failed')
      const data = await res.json()
      _accessToken = data.access_token
      return data.access_token
    })
    .finally(() => {
      _refreshPromise = null
    })

  return _refreshPromise
}

function getStoredRefreshToken() {
  return localStorage.getItem('refresh_token')
}

export function storeRefreshToken(token) {
  localStorage.setItem('refresh_token', token)
}

export function clearRefreshToken() {
  localStorage.removeItem('refresh_token')
}

export async function apiFetch(path, options = {}) {
  const activeOrg = localStorage.getItem('active_org_id')

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (_accessToken) {
    headers['Authorization'] = `Bearer ${_accessToken}`
  }

  if (activeOrg && !options.skipOrgHeader) {
    headers['X-Active-Org'] = activeOrg
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  // Token expired — attempt refresh and retry once
  if (res.status === 401 && getStoredRefreshToken()) {
    try {
      await refreshAccessToken()
      headers['Authorization'] = `Bearer ${_accessToken}`
      const retryRes = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers,
      })
      return retryRes
    } catch {
      // Refresh failed — clear auth state
      _accessToken = null
      clearRefreshToken()
      window.dispatchEvent(new Event('auth:logout'))
      throw new Error('Session expired')
    }
  }

  return res
}

export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options)
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const err = await res.json()
      detail = err.detail?.message || err.detail || detail
    } catch {}
    const error = new Error(detail)
    error.status = res.status
    throw error
  }
  // 204 No Content
  if (res.status === 204) return null
  return res.json()
}