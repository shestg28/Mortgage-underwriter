import { useEffect, useState } from 'react'
import client from '../api/client'
import { getApplicationId } from '../utils/workflowStorage'

function DecisionResultsPage() {
  const [applicationId, setApplicationId] = useState(getApplicationId())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (applicationId) {
      fetchDecision(applicationId)
    }
  }, [applicationId])

  const fetchDecision = async (appId) => {
    setLoading(true)
    setError(null)
    try {
      const response = await client.get(`/api/applications/${encodeURIComponent(appId)}`)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch decision results.')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    if (applicationId) fetchDecision(applicationId)
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-2xl font-semibold text-slate-900 mb-2">Decision Results</h3>
          <p className="text-sm text-slate-500">Final application decision, risk score, and fraud summary.</p>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Refresh
        </button>
      </div>

      {!applicationId && (
        <div className="mt-6 rounded-2xl bg-slate-50 p-6 text-sm text-slate-600">No application ID found in workflow. Create an application first.</div>
      )}

      {error && <div className="mt-6 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {loading && <div className="mt-6 text-sm text-slate-600">Loading decision results...</div>}

      {result && (
        <div className="mt-6 space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Risk Score</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{result.risk_score ?? 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Final Decision</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900 capitalize">{result.decision || 'N/A'}</p>
            </div>
          </div>
          <div className="rounded-2xl bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">Fraud Flags</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">{result.audits?.filter((audit) => audit.event_type === 'application_analyzed').length ?? 0}</p>
            <p className="mt-2 text-sm text-slate-600">Review application audit details for fraud flag history.</p>
          </div>
          <div className="rounded-2xl bg-white p-4 shadow-sm">
            <h4 className="text-base font-semibold text-slate-900">Decision Notes</h4>
            <p className="mt-2 text-sm text-slate-600">{result.decision_reason || 'No decision details available yet.'}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default DecisionResultsPage
