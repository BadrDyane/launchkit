// launchkit/frontend/src/components/common/Spinner.jsx
export default function Spinner({ size = 24 }) {
    return (
      <div
        style={{
          width: size,
          height: size,
          border: '2px solid var(--color-border)',
          borderTop: '2px solid var(--color-accent)',
          borderRadius: '50%',
          animation: 'spin 0.7s linear infinite',
        }}
      />
    )
  }