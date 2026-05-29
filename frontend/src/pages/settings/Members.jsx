// launchkit/frontend/src/pages/settings/Members.jsx
import { useEffect, useState } from 'react'
import { getInvitations, getMembers, inviteMember, removeMember, revokeInvitation, updateMemberRole } from '../../api/org.js'
import { useAuth } from '../../context/AuthContext.jsx'
import AppLayout from '../../components/layout/AppLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Button from '../../components/common/Button.jsx'
import Badge from '../../components/common/Badge.jsx'
import Input from '../../components/common/Input.jsx'
import ErrorMessage from '../../components/common/ErrorMessage.jsx'
import Spinner from '../../components/common/Spinner.jsx'

export default function Members() {
  const { user } = useAuth()
  const [members, setMembers] = useState([])
  const [invitations, setInvitations] = useState([])
  const [loading, setLoading] = useState(true)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [inviting, setInviting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadData = async () => {
    try {
      const [m, i] = await Promise.all([getMembers(), getInvitations()])
      setMembers(m)
      setInvitations(i)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleInvite = async () => {
    if (!inviteEmail) return setError('Email is required')
    setError('')
    setInviting(true)
    try {
      await inviteMember(inviteEmail, inviteRole)
      setSuccess(`Invitation sent to ${inviteEmail}`)
      setInviteEmail('')
      await loadData()
    } catch (err) {
      setError(err.message)
    } finally {
      setInviting(false)
    }
  }

  const roleVariant = { owner: 'accent', admin: 'success', member: 'default' }

  if (loading) return <AppLayout><div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}><Spinner /></div></AppLayout>

  return (
    <AppLayout>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
        Members
      </h1>

      <Card style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 16 }}>Invite member</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <Input label="Email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder="colleague@example.com" />
          </div>
          <select
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value)}
            style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)', padding: '10px 14px', fontSize: '14px' }}
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            <option value="owner">Owner</option>
          </select>
          <Button onClick={handleInvite} loading={inviting}>Send invite</Button>
        </div>
        {error && <div style={{ marginTop: 12 }}><ErrorMessage message={error} /></div>}
        {success && <div style={{ marginTop: 12, fontSize: '13px', color: 'var(--color-success)' }}>{success}</div>}
      </Card>

      <Card style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 16 }}>Team ({members.length})</h3>
        {members.map((m) => (
          <div key={m.user_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--color-border)' }}>
            <div>
              <div style={{ fontSize: '14px', color: 'var(--color-text-primary)', fontWeight: 500 }}>{m.display_name || m.email}</div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{m.email}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Badge variant={roleVariant[m.role_name] || 'default'}>{m.role_name}</Badge>
              {m.user_id !== user?.id && m.role_name !== 'owner' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm('Remove this member?')) return
                    await removeMember(m.user_id)
                    await loadData()
                  }}
                >
                  Remove
                </Button>
              )}
            </div>
          </div>
        ))}
      </Card>

      {invitations.length > 0 && (
        <Card>
          <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 16 }}>Pending invitations</h3>
          {invitations.map((inv) => (
            <div key={inv.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--color-border)' }}>
              <div>
                <div style={{ fontSize: '14px', color: 'var(--color-text-primary)' }}>{inv.email}</div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Role: {inv.role_name} · Expires {new Date(inv.expires_at).toLocaleDateString()}</div>
              </div>
              <Button variant="ghost" size="sm" onClick={async () => { await revokeInvitation(inv.id); await loadData() }}>
                Revoke
              </Button>
            </div>
          ))}
        </Card>
      )}
    </AppLayout>
  )
}