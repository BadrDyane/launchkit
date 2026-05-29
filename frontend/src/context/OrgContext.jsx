// launchkit/frontend/src/context/OrgContext.jsx
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMyOrgs } from '../api/org.js'
import { useAuth } from './AuthContext.jsx'

const OrgContext = createContext(null)

export function OrgProvider({ children }) {
  const { user } = useAuth()
  const [orgs, setOrgs] = useState([])
  const [activeOrg, setActiveOrg] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadOrgs = useCallback(async () => {
    if (!user) return
    setLoading(true)
    try {
      const data = await getMyOrgs()
      setOrgs(data)

      // Restore previously active org or default to first
      const storedId = window.localStorage.getItem('active_org_id')
      const found = storedId ? data.find((o) => o.id === storedId) : null
      const selected = found || data[0] || null
      setActiveOrg(selected)
      if (selected) window.localStorage.setItem('active_org_id', selected.id)
    } catch {
      setOrgs([])
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    if (user) loadOrgs()
    else {
      setOrgs([])
      setActiveOrg(null)
    }
  }, [user, loadOrgs])

  const switchOrg = useCallback((org) => {
    setActiveOrg(org)
    window.localStorage.setItem('active_org_id', org.id)
  }, [])

  return (
    <OrgContext.Provider value={{ orgs, activeOrg, loading, loadOrgs, switchOrg }}>
      {children}
    </OrgContext.Provider>
  )
}

export function useOrg() {
  const ctx = useContext(OrgContext)
  if (!ctx) throw new Error('useOrg must be used within OrgProvider')
  return ctx
}