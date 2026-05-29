// launchkit/frontend/src/components/layout/AuthLayout.jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import Spinner from '../common/Spinner.jsx'

export default function AuthLayout({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <Spinner size={32} />
      </div>
    )
  }

  if (user) return <Navigate to="/dashboard" replace />

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-background)',
        padding: 24,
      }}
    >
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '28px',
              color: 'var(--color-accent)',
              marginBottom: 8,
            }}
          >
            MeetingMind
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
            AI-powered meeting intelligence
          </p>
        </div>
        {children}
      </div>
    </div>
  )
}