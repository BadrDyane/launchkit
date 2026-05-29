// launchkit/frontend/src/pages/auth/Signup.jsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import AuthLayout from '../../components/layout/AuthLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Input from '../../components/common/Input.jsx'
import Button from '../../components/common/Button.jsx'
import ErrorMessage from '../../components/common/ErrorMessage.jsx'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!email || !password) return setError('Email and password are required')
    setError('')
    setLoading(true)
    try {
      await signup(email, password, name)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Card>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', marginBottom: 24, color: 'var(--color-text-primary)' }}>
          Create account
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Input label="Name" id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Alex Chen" />
          <Input label="Email" id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          <Input label="Password" id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="8+ chars, upper, lower, number" />
          <ErrorMessage message={error} />
          <Button onClick={handleSubmit} loading={loading} fullWidth>
            Create account
          </Button>
        </div>
        <div style={{ marginTop: 20, fontSize: '13px', color: 'var(--color-text-secondary)', textAlign: 'center' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--color-accent)' }}>Sign in</Link>
        </div>
      </Card>
    </AuthLayout>
  )
}