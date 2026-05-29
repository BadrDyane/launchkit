// launchkit/frontend/src/context/AuthContext.jsx
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, logout as apiLogout, signup as apiSignup } from '../api/auth.js'
import {
  clearRefreshToken,
  setAccessToken,
  storeRefreshToken,
} from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = window.localStorage.getItem('refresh_token')
    if (!stored) {
      setLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => { clearRefreshToken() })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const handler = () => {
      setUser(null)
      window.localStorage.removeItem('active_org_id')
    }
    window.addEventListener('auth:logout', handler)
    return () => window.removeEventListener('auth:logout', handler)
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password)
    setAccessToken(data.access_token)
    if (data.refresh_token) storeRefreshToken(data.refresh_token)
    setUser(data.user)
    return data
  }, [])

  const signup = useCallback(async (email, password, displayName) => {
    const data = await apiSignup(email, password, displayName)
    setAccessToken(data.access_token)
    if (data.refresh_token) storeRefreshToken(data.refresh_token)
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = window.localStorage.getItem('refresh_token')
    try { if (refreshToken) await apiLogout(refreshToken) } catch {}
    setAccessToken(null)
    clearRefreshToken()
    window.localStorage.removeItem('active_org_id')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}