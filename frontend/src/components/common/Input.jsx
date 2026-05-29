// launchkit/frontend/src/components/common/Input.jsx
export default function Input({ label, error, id, ...props }) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {label && (
          <label
            htmlFor={id}
            style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: 500 }}
          >
            {label}
          </label>
        )}
        <input
          id={id}
          style={{
            background: 'var(--color-surface-2)',
            border: `1px solid ${error ? 'var(--color-danger)' : 'var(--color-border)'}`,
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-primary)',
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            padding: '10px 14px',
            outline: 'none',
            width: '100%',
            boxSizing: 'border-box',
          }}
          {...props}
        />
        {error && (
          <span style={{ fontSize: '12px', color: 'var(--color-danger)' }}>{error}</span>
        )}
      </div>
    )
  }