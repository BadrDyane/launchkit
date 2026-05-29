// launchkit/frontend/src/components/billing/UsageBar.jsx
export default function UsageBar({ used, limit, isUnlimited }) {
    const pct = isUnlimited ? 0 : Math.min(100, (used / limit) * 100)
    const color = pct >= 90 ? 'var(--color-danger)' : pct >= 70 ? 'var(--color-warning)' : 'var(--color-accent)'
  
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '13px' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>AI calls this month</span>
          <span style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
            {isUnlimited ? `${used} / ∞` : `${used} / ${limit}`}
          </span>
        </div>
        {!isUnlimited && (
          <div
            style={{
              height: 6,
              background: 'var(--color-surface-2)',
              borderRadius: 999,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${pct}%`,
                background: color,
                borderRadius: 999,
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        )}
      </div>
    )
  }