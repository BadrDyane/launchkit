// launchkit/frontend/src/components/common/Button.jsx
export default function Button({
    children,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    fullWidth = false,
    onClick,
    type = 'button',
    ...props
  }) {
    const styles = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      borderRadius: 'var(--radius-md)',
      fontFamily: 'var(--font-body)',
      fontWeight: 500,
      cursor: disabled || loading ? 'not-allowed' : 'pointer',
      opacity: disabled || loading ? 0.6 : 1,
      border: 'none',
      transition: 'all 0.15s ease',
      width: fullWidth ? '100%' : 'auto',
      padding: size === 'sm' ? '6px 12px' : size === 'lg' ? '14px 28px' : '10px 20px',
      fontSize: size === 'sm' ? '13px' : size === 'lg' ? '16px' : '14px',
      ...(variant === 'primary' && {
        background: 'var(--color-accent)',
        color: '#08080F',
      }),
      ...(variant === 'secondary' && {
        background: 'var(--color-surface-2)',
        color: 'var(--color-text-primary)',
        border: '1px solid var(--color-border)',
      }),
      ...(variant === 'danger' && {
        background: 'var(--color-danger)',
        color: '#fff',
      }),
      ...(variant === 'ghost' && {
        background: 'transparent',
        color: 'var(--color-text-secondary)',
        border: '1px solid var(--color-border)',
      }),
    }
  
    return (
      <button type={type} style={styles} onClick={onClick} disabled={disabled || loading} {...props}>
        {loading ? <span>Loading…</span> : children}
      </button>
    )
  }