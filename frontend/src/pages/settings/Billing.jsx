// launchkit/frontend/src/pages/settings/Billing.jsx
import { useEffect, useState } from 'react'
import { createCheckout, createPortal, getBillingStatus } from '../../api/billing.js'
import { getUsage } from '../../api/ai.js'
import { useOrg } from '../../context/OrgContext.jsx'
import AppLayout from '../../components/layout/AppLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Button from '../../components/common/Button.jsx'
import Badge from '../../components/common/Badge.jsx'
import UsageBar from '../../components/billing/UsageBar.jsx'
import ErrorMessage from '../../components/common/ErrorMessage.jsx'
import Spinner from '../../components/common/Spinner.jsx'

const PLANS = [
  { name: 'Free', slug: 'free', price: '$0/mo', calls: '10 AI calls/month', priceId: null },
  { name: 'Pro', slug: 'pro', price: '$15/mo', calls: '100 AI calls/month', priceId: import.meta.env.VITE_STRIPE_PRO_PRICE_ID },
  { name: 'Business', slug: 'business', price: '$49/mo', calls: 'Unlimited AI calls', priceId: import.meta.env.VITE_STRIPE_BUSINESS_PRICE_ID },
]

export default function Billing() {
  const { activeOrg } = useOrg()
  const [billing, setBilling] = useState(null)
  const [usage, setUsage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [portalLoading, setPortalLoading] = useState(false)
  const [checkoutLoading, setCheckoutLoading] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!activeOrg) {
      setLoading(false)
      return
    }
    Promise.all([getBillingStatus(), getUsage()])
      .then(([b, u]) => { setBilling(b); setUsage(u) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [activeOrg])

  if (loading) {
    return (
      <AppLayout>
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <Spinner />
        </div>
      </AppLayout>
    )
  }

  if (!activeOrg) {
    return (
      <AppLayout>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
          Billing
        </h1>
        <Card>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
            No workspace available.
          </p>
        </Card>
      </AppLayout>
    )
  }

  const handlePortal = async () => {
    setPortalLoading(true)
    try {
      const { portal_url } = await createPortal()
      window.location.href = portal_url
    } catch (err) {
      setError(err.message)
      setPortalLoading(false)
    }
  }

  const handleCheckout = async (priceId) => {
    if (!priceId) return
    setCheckoutLoading(priceId)
    try {
      const { checkout_url } = await createCheckout(priceId)
      window.location.href = checkout_url
    } catch (err) {
      setError(err.message)
      setCheckoutLoading(null)
    }
  }

  const statusVariant = {
    free: 'default', active: 'success', trialing: 'accent',
    past_due: 'warning', canceled: 'danger', expired: 'danger',
  }

  return (
    <AppLayout>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
        Billing
      </h1>

      {error && <div style={{ marginBottom: 16 }}><ErrorMessage message={error} /></div>}

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              {billing?.plan_name} Plan
            </div>
            <Badge variant={statusVariant[billing?.subscription_status] || 'default'}>
              {billing?.subscription_status}
            </Badge>
          </div>
          {billing?.stripe_customer_id && (
            <Button variant="secondary" onClick={handlePortal} loading={portalLoading}>
              Manage Subscription
            </Button>
          )}
        </div>
        {usage && (
          <UsageBar
            used={usage.ai_calls_used}
            limit={usage.ai_calls_limit}
            isUnlimited={usage.is_unlimited}
          />
        )}
      </Card>

      <h3 style={{ fontSize: '16px', color: 'var(--color-text-primary)', marginBottom: 16 }}>Plans</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {PLANS.map((plan) => {
          const isCurrent = billing?.plan_slug === plan.slug
          return (
            <Card
              key={plan.slug}
              style={{ border: isCurrent ? '1px solid var(--color-accent)' : '1px solid var(--color-border)' }}
            >
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '18px', color: 'var(--color-text-primary)', marginBottom: 4 }}>
                {plan.name}
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-accent)', marginBottom: 8 }}>
                {plan.price}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: 20 }}>
                {plan.calls}
              </div>
              {isCurrent ? (
                <Badge variant="accent">Current plan</Badge>
              ) : plan.priceId ? (
                <Button
                  variant="primary"
                  size="sm"
                  loading={checkoutLoading === plan.priceId}
                  onClick={() => handleCheckout(plan.priceId)}
                >
                  Upgrade
                </Button>
              ) : null}
            </Card>
          )
        })}
      </div>
    </AppLayout>
  )
}