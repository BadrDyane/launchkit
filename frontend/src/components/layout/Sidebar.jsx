// launchkit/frontend/src/components/layout/Sidebar.jsx
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import { useOrg } from '../../context/OrgContext.jsx'

const NAV = [
  { label: 'Dashboard', path: '/dashboard', icon: '▦' },
  { label: 'Summarizer', path: '/ai', icon: '✦' },
  { label: 'Members', path: '/settings/members', icon: '◈' },
  { label: 'Billing', path: '/settings/billing', icon: '◎' },
  { label: 'Settings', path: '/settings/profile', icon: '⚙' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const { activeOrg, orgs, switchOrg } = useOrg()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside
      style={{
        width: 220,
        minHeight: '100vh',
        background: 'var(--color-surface)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: '0 20px 24px', borderBottom: '1px solid var(--color-border)' }}>
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '18px',
            fontWeight: 700,
            color: 'var(--color-accent)',
          }}
        >
          MeetingMind
        </span>
      </div>

      {/* Org switcher */}
      {orgs.length > 0 && (
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Workspace
          </div>
          <select
            value={activeOrg?.id || ''}
            onChange={(e) => {
              const org = orgs.find((o) => o.id === e.target.value)
              if (org) switchOrg(org)
            }}
            style={{
              width: '100%',
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-primary)',
              fontSize: '13px',
              padding: '6px 10px',
              cursor: 'pointer',
            }}
          >
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>{o.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Nav */}
      <nav style={{ flex: 1, padding: '16px 12px' }}>
        {NAV.map(({ label, path, icon }) => {
          const active = location.pathname.startsWith(path)
          return (
            <Link
              key={path}
              to={path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '9px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '14px',
                color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                background: active ? 'var(--color-accent-dim)' : 'transparent',
                textDecoration: 'none',
                marginBottom: 2,
                fontWeight: active ? 500 : 400,
                transition: 'all 0.1s',
              }}
            >
              <span>{icon}</span>
              {label}
            </Link>
          )
        })}

        {user?.is_superadmin && (
          <Link
            to="/admin"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '9px 12px',
              borderRadius: 'var(--radius-md)',
              fontSize: '14px',
              color: location.pathname.startsWith('/admin') ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              background: location.pathname.startsWith('/admin') ? 'var(--color-accent-dim)' : 'transparent',
              textDecoration: 'none',
              marginBottom: 2,
              marginTop: 8,
              borderTop: '1px solid var(--color-border)',
              paddingTop: 16,
            }}
          >
            <span>⚡</span>
            Admin
          </Link>
        )}
      </nav>

      {/* User */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--color-border)' }}>
        <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', fontWeight: 500, marginBottom: 4 }}>
          {user?.display_name || user?.email}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: 12 }}>
          {user?.email}
        </div>
        <button
          onClick={handleLogout}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-secondary)',
            fontSize: '13px',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          Sign out →
        </button>
      </div>
    </aside>
  )
}