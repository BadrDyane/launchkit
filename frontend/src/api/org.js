// launchkit/frontend/src/api/org.js
import { apiJson } from './client.js'

export async function getMyOrgs() {
  return apiJson('/org/my-orgs', { skipOrgHeader: true })
}

export async function getOrg() {
  return apiJson('/org/')
}

export async function updateOrg(name) {
  return apiJson('/org/', { method: 'PATCH', body: JSON.stringify({ name }) })
}

export async function getMembers() {
  return apiJson('/org/members')
}

export async function updateMemberRole(userId, roleName) {
  return apiJson(`/org/members/${userId}/role`, {
    method: 'PATCH',
    body: JSON.stringify({ role_name: roleName }),
  })
}

export async function removeMember(userId) {
  return apiJson(`/org/members/${userId}`, { method: 'DELETE' })
}

export async function inviteMember(email, roleName) {
  return apiJson('/org/invitations', {
    method: 'POST',
    body: JSON.stringify({ email, role_name: roleName }),
  })
}

export async function getInvitations() {
  return apiJson('/org/invitations')
}

export async function revokeInvitation(invitationId) {
  return apiJson(`/org/invitations/${invitationId}`, { method: 'DELETE' })
}

export async function acceptInvitation(token) {
  return apiJson('/org/invitations/accept', {
    method: 'POST',
    body: JSON.stringify({ token }),
    skipOrgHeader: true,
  })
}