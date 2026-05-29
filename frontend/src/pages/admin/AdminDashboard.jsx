// launchkit/frontend/src/pages/admin/AdminDashboard.jsx
import { useEffect, useState } from 'react'
import { getAdminOrgs, getAdminStats, getAdminUsers } from '../../api/admin.js'
import AppLayout from '../../components/layout/AppLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Badge from '../../components/common/Badge.jsx'
import Spinner from '../../components/common/Spinner.jsx'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [orgs, setOrgs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getAdminStats(), getAdminUsers(), getAdminOrgs()])
      .then(([s, u, o]) => { setStats(s); setUsers(u); setOrgs(o) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <AppLayout><div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}><Spinner /></div></AppLayout>

  return (
    <AppLayout>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
        ⚡ Admin Panel
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Users', value: stats?.total_users },
          { label: 'Orgs', value: stats?.total_orgs },
          { label: 'Active Subs', value: stats?.active_subscriptions },
          { label: 'Free', value: stats?.free_orgs },
          { label: 'Past Due', value: stats?.past_due_orgs },
        ].map(({ label, value }) => (
          <Card key={label} padding="16px">
            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
            <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)' }}>{value}</div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Card>
          <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 16 }}>Recent Users</h3>
          {users.slice(0, 8).map((u) => (
            <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--color-border)', fontSize: '13px' }}>
              <div>
                <div style={{ color: 'var(--color-text-primary)' }}>{u.email}</div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '11px' }}>{new Date(u.created_at).toLocaleDateString()}</div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {u.is_superadmin && <Badge variant="accent">admin</Badge>}
                {!u.is_active && <Badge variant="danger">disabled</Badge>}
              </div>
            </div>
          ))}
        </Card>

        <Card>
          <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 16 }}>Organizations</h3>
          {orgs.slice(0, 8).map((o) => (
            <div key={o.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--color-border)', fontSize: '13px' }}>
              <div>
                <div style={{ color: 'var(--color-text-primary)' }}>{o.name}</div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '11px' }}>{o.plan_name} · {o.member_count} members</div>
              </div>
              <Badge variant={o.subscription_status === 'active' ? 'success' : 'default'}>
                {o.subscription_status}
              </Badge>
            </div>
          ))}
        </Card>
      </div>
    </AppLayout>
  )
}