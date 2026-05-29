// launchkit/frontend/src/pages/ai/Summarize.jsx
import { useEffect, useState } from 'react'
import { getSummaries, summarize } from '../../api/ai.js'
import { useOrg } from '../../context/OrgContext.jsx'
import AppLayout from '../../components/layout/AppLayout.jsx'
import Card from '../../components/common/Card.jsx'
import Button from '../../components/common/Button.jsx'
import ErrorMessage from '../../components/common/ErrorMessage.jsx'
import Spinner from '../../components/common/Spinner.jsx'

function SummaryCard({ summary }) {
  return (
    <Card style={{ marginBottom: 16 }}>
      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: 8 }}>
        {new Date(summary.created_at).toLocaleString()} · {summary.participants?.join(', ')}
      </div>
      <p style={{ color: 'var(--color-text-primary)', fontSize: '14px', lineHeight: 1.6, marginBottom: 12 }}>
        {summary.summary}
      </p>
      {summary.action_items?.length > 0 && (
        <div>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Action Items
          </div>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {summary.action_items.map((item, i) => (
              <li key={i} style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: 4 }}>
                {item.task}{item.owner ? ` — ${item.owner}` : ''}{item.due_date ? ` (${item.due_date})` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
      {summary.key_decisions?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Key Decisions
          </div>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {summary.key_decisions.map((d, i) => (
              <li key={i} style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: 4 }}>{d}</li>
            ))}
          </ul>
        </div>
      )}
      <div style={{ marginTop: 12, fontSize: '11px', color: 'var(--color-text-secondary)' }}>
        {summary.tokens_in + summary.tokens_out} tokens · ${summary.cost_usd?.toFixed(6)}
      </div>
    </Card>
  )
}

export default function Summarize() {
  const { activeOrg } = useOrg()
  const [transcript, setTranscript] = useState('')
  const [result, setResult] = useState(null)
  const [summaries, setSummaries] = useState([])
  const [loading, setLoading] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!activeOrg) {
      setListLoading(false)
      return
    }
    getSummaries()
      .then(setSummaries)
      .catch(console.error)
      .finally(() => setListLoading(false))
  }, [activeOrg])

  if (!activeOrg) {
    return (
      <AppLayout>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
          Meeting Summarizer
        </h1>
        <Card>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
            No workspace available.
          </p>
        </Card>
      </AppLayout>
    )
  }

  const handleSummarize = async () => {
    if (!transcript.trim()) return setError('Please paste a transcript')
    if (transcript.trim().length < 50) return setError('Transcript must be at least 50 characters')
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const data = await summarize(transcript)
      setResult(data)
      setSummaries((prev) => [data, ...prev])
      setTranscript('')
    } catch (err) {
      if (err.status === 402) {
        setError('Monthly AI call limit reached. Upgrade your plan to continue.')
      } else {
        setError(err.message || 'Summarization failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppLayout>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', color: 'var(--color-text-primary)', marginBottom: 24 }}>
        Meeting Summarizer
      </h1>

      <Card style={{ marginBottom: 32 }}>
        <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 12 }}>
          Paste your transcript
        </h3>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Paste your meeting transcript here (minimum 50 characters)..."
          style={{
            width: '100%', minHeight: 180, background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-primary)', fontFamily: 'var(--font-body)',
            fontSize: '14px', padding: '12px', resize: 'vertical',
            boxSizing: 'border-box', outline: 'none', lineHeight: 1.6,
          }}
        />
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button onClick={handleSummarize} loading={loading} disabled={!transcript.trim()}>
            ✦ Summarize
          </Button>
          {transcript && (
            <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              {transcript.length} characters
            </span>
          )}
        </div>
        {error && <div style={{ marginTop: 12 }}><ErrorMessage message={error} /></div>}
      </Card>

      {result && (
        <div style={{ marginBottom: 32 }}>
          <h3 style={{ fontSize: '15px', color: 'var(--color-accent)', marginBottom: 12 }}>✦ Latest Result</h3>
          <SummaryCard summary={result} />
        </div>
      )}

      <div>
        <h3 style={{ fontSize: '15px', color: 'var(--color-text-primary)', marginBottom: 16 }}>
          Past Summaries
        </h3>
        {listLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner /></div>
        ) : summaries.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>No summaries yet.</p>
        ) : (
          summaries.filter((s) => s.id !== result?.id).map((s) => <SummaryCard key={s.id} summary={s} />)
        )}
      </div>
    </AppLayout>
  )
}