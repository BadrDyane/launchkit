// launchkit/frontend/src/components/common/Badge.jsx
export default function Badge({ children, variant = 'default' }) {
    const colors = {
      default: { bg: 'var(--color-surface-2)', color: 'var(--color-text-secondary)' },
      success: { bg: 'rgba(0,200,150,0.15)', color: 'var(--color-success)' },
      danger: { bg: 'rgba(255,77,106,0.15)', color: 'var(--color-danger)' },
      warning: { bg: 'rgba(255,179,71,0.15)', color: 'var(--color-warning)' },
      accent: { bg: 'var(--color-accent-dim)', color: 'var(--color-accent)' },
    }
    const c = colors[variant] || colors.default
    return (
      <span
        style={{
          display: 'inline-block',
          padding: '2px 10px',
          borderRadius: '999px',
          fontSize: '12px',
          fontWeight: 500,
          background: c.bg,
          color: c.color,
        }}
      >
        {children}
      </span>
    )
  }