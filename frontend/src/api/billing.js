// launchkit/frontend/src/api/billing.js
import { apiJson } from './client.js'

export async function getBillingStatus() {
  return apiJson('/billing/status')
}

export async function createCheckout(priceId) {
  return apiJson('/billing/checkout', {
    method: 'POST',
    body: JSON.stringify({ price_id: priceId }),
  })
}

export async function createPortal() {
  return apiJson('/billing/portal', { method: 'POST' })
}