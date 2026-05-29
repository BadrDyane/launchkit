// launchkit/frontend/src/api/admin.js
import { apiJson } from './client.js'

export async function getAdminStats() {
  return apiJson('/admin/stats', { skipOrgHeader: true })
}

export async function getAdminUsers(page = 1) {
  return apiJson(`/admin/users?page=${page}`, { skipOrgHeader: true })
}

export async function getAdminOrgs(page = 1) {
  return apiJson(`/admin/orgs?page=${page}`, { skipOrgHeader: true })
}

export async function disableUser(userId) {
  return apiJson(`/admin/users/${userId}/disable`, {
    method: 'POST',
    skipOrgHeader: true,
  })
}

export async function enableUser(userId) {
  return apiJson(`/admin/users/${userId}/enable`, {
    method: 'POST',
    skipOrgHeader: true,
  })
}

export async function overrideSubscription(orgId, planSlug, status) {
  return apiJson(`/admin/orgs/${orgId}/subscription-override`, {
    method: 'POST',
    body: JSON.stringify({ plan_slug: planSlug, subscription_status: status }),
    skipOrgHeader: true,
  })
}

export async function getAuditLogs(page = 1, eventType = null) {
  const params = new URLSearchParams({ page })
  if (eventType) params.set('event_type', eventType)
  return apiJson(`/admin/audit-logs?${params}`, { skipOrgHeader: true })
}