// launchkit/frontend/src/pages/auth/Login.jsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import AuthLayout from '../../components/layout/AuthLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Input from '../../components/common/Input.jsx'
import Button from '../../components/common/Button.jsx'
import ErrorMessage from '../../components/common/ErrorMessage.jsx'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!email || !password) return setError('Please fill in all fields')
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Card>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', marginBottom: 24, color: 'var(--color-text-primary)' }}>
          Sign in
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Input
            label="Email"
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <Input
            label="Password"
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
          <ErrorMessage message={error} />
          <Button onClick={handleSubmit} loading={loading} fullWidth>
            Sign in
          </Button>
        </div>
        <div style={{ marginTop: 20, fontSize: '13px', color: 'var(--color-text-secondary)', textAlign: 'center' }}>
          <Link to="/forgot-password" style={{ color: 'var(--color-accent)' }}>
            Forgot password?
          </Link>
          {' · '}
          <Link to="/signup" style={{ color: 'var(--color-accent)' }}>
            Create account
          </Link>
        </div>
      </Card>
    </AuthLayout>
  )
}