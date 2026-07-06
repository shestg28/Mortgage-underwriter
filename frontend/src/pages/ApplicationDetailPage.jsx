import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import client from '../api/client'

function ApplicationDetailPage() {
  const { applicationId } = useParams()
  const [application, setApplication] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [decisionStatus, setDecisionStatus] = useState('')
  const [statusChangeError, setStatusChangeError] = useState(null)
  const [statusChangeSuccess, setStatusChangeSuccess] = useState(null)

  useEffect(() => {
    const fetchApplication = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await client.get(`/api/applications/${encodeURIComponent(applicationId)}`)
        setApplication(response.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load application.')
      } finally {
        setLoading(false)
      }
    }

    if (applicationId) {
      fetchApplication()
    }
  }, [applicationId])

  const handleDecisionSubmit = async (event) => {
    event.preventDefault()
    setStatusChangeError(null)
    setStatusChangeSuccess(null)

    if (!decisionStatus) {
      setStatusChangeError('Select approve or reject before submitting.')
      return
    }

    try {
      const response = await client.post(`/api/applications/${encodeURIComponent(applicationId)}/decision`, {
        status: decisionStatus,
      })
      setApplication(response.data)
      setStatusChangeSuccess('Application status updated successfully.')
    } catch (err) {
      setStatusChangeError(err.response?.data?.detail || 'Failed to update application status.')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-2xl font-semibold text-slate-900">Review Application</h3>
          <p className="text-sm text-slate-500">Review AI results, fraud flags, and approve or reject.</p>
        </div>
      </div>

      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {loading && <div className="text-sm text-slate-600">Loading application...</div>}

      {application && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-slate-50 p-5 shadow-sm">
              <p className="text-sm text-slate-500">Application ID</p>
              <p className="mt-2 text-base font-semibold text-slate-900 break-words">{application.id}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5 shadow-sm">
              <p className="text-sm text-slate-500">Customer Name</p>
              <p className="mt-2 text-base font-semibold text-slate-900">{application.customer_name || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5 shadow-sm">
              <p className="text-sm text-slate-500">Customer ID</p>
              <p className="mt-2 text-base font-semibold text-slate-900">{application.customer_id}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5 shadow-sm">
              <p className="text-sm text-slate-500">Status</p>
              <p className="mt-2 text-base font-semibold text-slate-900 capitalize">{application.status}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5 shadow-sm">
              <p className="text-sm text-slate-500">Decision</p>
              <p className="mt-2 text-base font-semibold text-slate-900 capitalize">{application.decision || 'Pending'}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5 shadow-sm">
              <p className="text-sm text-slate-500">Risk Score</p>
              <p className="mt-2 text-base font-semibold text-slate-900">{application.risk_score ?? 'N/A'}</p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
            <h4 className="text-lg font-semibold text-slate-900 mb-3">Decision Notes</h4>
            <p className="text-sm text-slate-600">{application.decision_reason || 'No decision details available yet.'}</p>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
            <h4 className="text-lg font-semibold text-slate-900 mb-4">Update Application Status</h4>
            <form onSubmit={handleDecisionSubmit} className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex items-center gap-3 rounded-2xl border border-slate-300 bg-white px-4 py-4">
                  <input
                    type="radio"
                    name="status"
                    value="approved"
                    checked={decisionStatus === 'approved'}
                    onChange={(e) => setDecisionStatus(e.target.value)}
                    className="h-4 w-4 accent-indigo-600"
                  />
                  <span className="text-sm font-medium text-slate-700">Approve</span>
                </label>
                <label className="flex items-center gap-3 rounded-2xl border border-slate-300 bg-white px-4 py-4">
                  <input
                    type="radio"
                    name="status"
                    value="rejected"
                    checked={decisionStatus === 'rejected'}
                    onChange={(e) => setDecisionStatus(e.target.value)}
                    className="h-4 w-4 accent-indigo-600"
                  />
                  <span className="text-sm font-medium text-slate-700">Reject</span>
                </label>
              </div>
              <button
                type="submit"
                className="rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700"
              >
                Submit Decision
              </button>
            </form>
            {statusChangeError && <div className="mt-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{statusChangeError}</div>}
            {statusChangeSuccess && <div className="mt-4 rounded bg-emerald-100 px-4 py-3 text-sm text-emerald-700">{statusChangeSuccess}</div>}
          </div>
        </div>
      )}
    </div>
  )
}

export default ApplicationDetailPage
