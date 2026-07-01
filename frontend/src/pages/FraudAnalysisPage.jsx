import { useState } from 'react'
import client from '../api/client'

function FraudAnalysisPage() {
  const [applicationId, setApplicationId] = useState('')
  const [flags, setFlags] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const getFieldName = (flagType) => {
    if (flagType.endsWith('_missing')) return flagType.replace('_missing', '')
    if (flagType.endsWith('_mismatch')) return flagType.replace('_mismatch', '')
    return flagType
  }

  const handleFetch = async (event) => {
    event.preventDefault()
    setError(null)
    setFlags([])

    if (!applicationId.trim()) {
      setError('Application ID is required.')
      return
    }

    try {
      setLoading(true)
      const response = await client.get('/api/fraud/flags/', {
        params: { application_id: applicationId.trim() },
      })
      setFlags(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch fraud analysis.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Fraud Analysis</h3>
      <form onSubmit={handleFetch} className="grid gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Application ID</label>
          <input
            value={applicationId}
            onChange={(e) => setApplicationId(e.target.value)}
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="Enter application ID"
            required
          />
        </div>
        <button
          type="submit"
          className="rounded-xl w-auto max-w-[10rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          {loading ? 'Loading...' : 'Fetch Fraud Flags'}
        </button>
      </form>

      {error && <div className="mt-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}

      {flags.length > 0 && (
        <div className="mt-6 overflow-x-auto rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <table className="min-w-full text-left text-sm text-slate-700">
            <thead>
              <tr>
                <th className="border-b px-4 py-3 font-semibold">Field Name</th>
                <th className="border-b px-4 py-3 font-semibold">Flag Type</th>
                <th className="border-b px-4 py-3 font-semibold">Match Status</th>
                <th className="border-b px-4 py-3 font-semibold">Severity</th>
                <th className="border-b px-4 py-3 font-semibold">Details</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((flag) => (
                <tr key={flag.id} className="even:bg-slate-100">
                  <td className="border-b px-4 py-3">{getFieldName(flag.flag_type)}</td>
                  <td className="border-b px-4 py-3">{flag.flag_type}</td>
                  <td className="border-b px-4 py-3">
                    {flag.details?.pan_match === false || flag.details?.aadhaar_match === false || flag.details?.name_match === false || flag.details?.salary_diff_pct ? 'Mismatch' : 'Missing/Review'}
                  </td>
                  <td className="border-b px-4 py-3">{flag.severity}</td>
                  <td className="border-b px-4 py-3 break-words">{JSON.stringify(flag.details)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {flags.length === 0 && !loading && !error && (
        <div className="mt-4 rounded bg-slate-100 px-4 py-3 text-sm text-slate-600">No fraud flags found yet.</div>
      )}
    </div>
  )
}

export default FraudAnalysisPage
