// launchkit/frontend/src/components/common/ErrorMessage.jsx
export default function ErrorMessage({ message }) {
    if (!message) return null
    return (
      <div
        style={{
          background: 'rgba(255,77,106,0.1)',
          border: '1px solid rgba(255,77,106,0.3)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--color-danger)',
          fontSize: '13px',
          padding: '10px 14px',
        }}
      >
        {message}
      </div>
    )
  }