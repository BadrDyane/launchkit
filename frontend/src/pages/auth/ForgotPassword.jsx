// launchkit/frontend/src/pages/auth/ForgotPassword.jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { requestPasswordReset } from '../../api/auth.js'
import AuthLayout from '../../components/layout/AuthLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Input from '../../components/common/Input.jsx'
import Button from '../../components/common/Button.jsx'
import ErrorMessage from '../../components/common/ErrorMessage.jsx'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!email) return setError('Email is required')
    setLoading(true)
    try {
      await requestPasswordReset(email)
      setSent(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Card>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', marginBottom: 8, color: 'var(--color-text-primary)' }}>
          Reset password
        </h2>
        {sent ? (
          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', marginBottom: 20 }}>
              If that email exists, a reset link has been sent. Check your inbox.
            </p>
            <Link to="/login" style={{ color: 'var(--color-accent)', fontSize: '14px' }}>← Back to login</Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', margin: 0 }}>
              Enter your email and we'll send a reset link.
            </p>
            <Input label="Email" id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            <ErrorMessage message={error} />
            <Button onClick={handleSubmit} loading={loading} fullWidth>Send reset link</Button>
            <Link to="/login" style={{ color: 'var(--color-text-secondary)', fontSize: '13px', textAlign: 'center' }}>← Back to login</Link>
          </div>
        )}
      </Card>
    </AuthLayout>
  )
}