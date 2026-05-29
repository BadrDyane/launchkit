// launchkit/frontend/src/pages/dashboard/Dashboard.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getUsage } from '../../api/ai.js'
import { getBillingStatus } from '../../api/billing.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useOrg } from '../../context/OrgContext.jsx'
import AppLayout from '../../components/layout/AppLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Badge from '../../components/common/Badge.jsx'
import UsageBar from '../../components/billing/UsageBar.jsx'
import Spinner from '../../components/common/Spinner.jsx'

function StatCard({ label, value, sub }) {
  return (
    <Card>
      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: '28px', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)', marginBottom: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{sub}</div>}
    </Card>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { activeOrg } = useOrg()
  const [usage, setUsage] = useState(null)
  const [billing, setBilling] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!activeOrg) {
      setLoading(false)
      return
    }
    Promise.all([getUsage(), getBillingStatus()])
      .then(([u, b]) => { setUsage(u); setBilling(b) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [activeOrg])

  const statusVariant = {
    free: 'default', active: 'success', trialing: 'accent',
    past_due: 'warning', canceled: 'danger', expired: 'danger',
  }

  if (loading) {
    return (
      <AppLayout>
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spinner />
        </div>
      </AppLayout>
    )
  }

  if (!activeOrg) {
    return (
      <AppLayout>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Welcome back, {user?.display_name || user?.email?.split('@')[0]}
          </h1>
        </div>
        <Card>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
            No workspace found for this account.
          </p>
        </Card>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 4 }}>
          Welcome back, {user?.display_name || user?.email?.split('@')[0]}
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
          {activeOrg?.name}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 24 }}>
        <StatCard
          label="Plan"
          value={billing?.plan_name || '—'}
          sub={
            <Badge variant={statusVariant[billing?.subscription_status] || 'default'}>
              {billing?.subscription_status}
            </Badge>
          }
        />
        <StatCard
          label="AI Calls Used"
          value={usage?.ai_calls_used ?? '—'}
          sub={usage?.is_unlimited ? 'Unlimited plan' : `of ${usage?.ai_calls_limit} this month`}
        />
        <StatCard
          label="Remaining"
          value={usage?.is_unlimited ? '∞' : (usage?.remaining ?? '—')}
          sub="AI calls available"
        />
      </div>

      {usage && (
        <Card style={{ marginBottom: 24 }}>
          <UsageBar
            used={usage.ai_calls_used}
            limit={usage.ai_calls_limit}
            isUnlimited={usage.is_unlimited}
          />
        </Card>
      )}

      <Card>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', color: 'var(--color-text-primary)', marginBottom: 16 }}>
          Quick actions
        </h3>
        <div style={{ display: 'flex', gap: 12 }}>
          <Link
            to="/ai"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '10px 20px', background: 'var(--color-accent)',
              color: '#08080F', borderRadius: 'var(--radius-md)',
              fontSize: '14px', fontWeight: 500, textDecoration: 'none',
            }}
          >
            ✦ New Summary
          </Link>
          <Link
            to="/settings/billing"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '10px 20px', background: 'var(--color-surface-2)',
              color: 'var(--color-text-primary)', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: '14px', textDecoration: 'none',
            }}
          >
            ◎ Manage Billing
          </Link>
        </div>
      </Card>
    </AppLayout>
  )
}