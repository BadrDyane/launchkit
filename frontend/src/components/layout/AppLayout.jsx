// launchkit/frontend/src/components/layout/AppLayout.jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import Spinner from '../common/Spinner.jsx'
import Sidebar from './Sidebar.jsx'

export default function AppLayout({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <Spinner size={32} />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main
        style={{
          flex: 1,
          padding: '40px',
          overflowY: 'auto',
          background: 'var(--color-background)',
        }}
      >
        {children}
      </main>
    </div>
  )
}