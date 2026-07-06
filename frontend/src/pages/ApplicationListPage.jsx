import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client'

function ApplicationListPage({ status, title }) {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchApplications = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await client.get('/api/applications', {
        params: { status },
      })
      setApplications(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load applications.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchApplications()
  }, [status])

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-2xl font-semibold text-slate-900">{title}</h3>
          <p className="text-sm text-slate-500">Review applications in the selected queue.</p>
        </div>
        <button
          type="button"
          onClick={fetchApplications}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Refresh
        </button>
      </div>

      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {loading && <div className="text-sm text-slate-600">Loading applications...</div>}

      {!loading && applications.length === 0 && (
        <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-600">No applications found in this queue.</div>
      )}

      {applications.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm text-slate-700">
            <thead>
              <tr>
                <th className="border-b px-4 py-3 font-semibold">Application ID</th>
                <th className="border-b px-4 py-3 font-semibold">Customer ID</th>
                <th className="border-b px-4 py-3 font-semibold">Status</th>
                <th className="border-b px-4 py-3 font-semibold">Decision</th>
                <th className="border-b px-4 py-3 font-semibold">Risk Score</th>
                <th className="border-b px-4 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr key={application.id} className="even:bg-slate-100">
                  <td className="border-b px-4 py-3">{application.id}</td>
                  <td className="border-b px-4 py-3">{application.customer_id}</td>
                  <td className="border-b px-4 py-3 capitalize">{application.status}</td>
                  <td className="border-b px-4 py-3 capitalize">{application.decision || 'Pending'}</td>
                  <td className="border-b px-4 py-3">{application.risk_score ?? 'N/A'}</td>
                  <td className="border-b px-4 py-3">
                    <Link
                      className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700"
                      to={`/applications/${encodeURIComponent(application.id)}`}
                    >
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default ApplicationListPage
