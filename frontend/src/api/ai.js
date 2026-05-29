// launchkit/frontend/src/api/ai.js
import { apiJson } from './client.js'

export async function summarize(transcript) {
  return apiJson('/ai/summarize', {
    method: 'POST',
    body: JSON.stringify({ transcript }),
  })
}

export async function getSummaries(page = 1) {
  return apiJson(`/ai/summaries?page=${page}`)
}

export async function getSummary(id) {
  return apiJson(`/ai/summaries/${id}`)
}

export async function getUsage() {
  return apiJson('/usage/')
}