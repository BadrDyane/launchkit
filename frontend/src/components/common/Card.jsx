// launchkit/frontend/src/components/common/Card.jsx
export default function Card({ children, style = {}, padding = '24px' }) {
    return (
      <div
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding,
          ...style,
        }}
      >
        {children}
      </div>
    )
  }
