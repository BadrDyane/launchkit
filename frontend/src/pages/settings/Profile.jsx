// launchkit/frontend/src/pages/settings/Profile.jsx
import { useAuth } from '../../context/AuthContext.jsx'
import AppLayout from '../../components/layout/AppLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Badge from '../../components/common/Badge.jsx'

export default function Profile() {
  const { user } = useAuth()

  return (
    <AppLayout>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
        Profile
      </h1>
      <Card style={{ maxWidth: 480 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {[
            { label: 'Name', value: user?.display_name || '—' },
            { label: 'Email', value: user?.email },
            { label: 'Email verified', value: user?.is_email_verified ? '✓ Verified' : '✗ Not verified' },
            { label: 'Account type', value: user?.is_superadmin ? <Badge variant="accent">Superadmin</Badge> : <Badge>User</Badge> },
          ].map(({ label, value }) => (
            <div key={label}>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
              <div style={{ fontSize: '14px', color: 'var(--color-text-primary)' }}>{value}</div>
            </div>
          ))}
        </div>
      </Card>
    </AppLayout>
  )
}