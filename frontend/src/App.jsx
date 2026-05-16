// launchkit/frontend/src/App.jsx
function App() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      flexDirection: 'column',
      gap: '12px',
    }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: 'var(--color-accent)' }}>
        LaunchKit
      </h1>
      <p style={{ color: 'var(--color-text-secondary)' }}>
        Phase 0 — skeleton running
      </p>
    </div>
  )
}

export default App