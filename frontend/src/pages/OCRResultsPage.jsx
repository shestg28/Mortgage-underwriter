import { useState } from 'react'
import client from '../api/client'

function OCRResultsPage() {
  const [fileId, setFileId] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [applicationId, setApplicationId] = useState('')
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFetch = async (event) => {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!fileId.trim()) {
      setError('Enter a file ID to fetch OCR results.')
      return
    }

    try {
      setLoading(true)
      const response = await client.post('/api/documents/process', null, {
        params: {
          file_id: fileId.trim(),
          customer_id: customerId.trim() || undefined,
          application_id: applicationId.trim() || undefined,
        },
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch OCR results.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">OCR Results</h3>
      <form onSubmit={handleFetch} className="grid gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">File ID</label>
          <input
            value={fileId}
            onChange={(e) => setFileId(e.target.value)}
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="Enter uploaded file ID"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Customer ID (optional)</label>
          <input
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="Enter customer ID to help matching"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Application ID (optional)</label>
          <input
            value={applicationId}
            onChange={(e) => setApplicationId(e.target.value)}
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="Enter application ID to attach results"
          />
        </div>
        <button
          type="submit"
          className="rounded-xl w-auto max-w-[10rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          {loading ? 'Fetching...' : 'Fetch OCR Results'}
        </button>
      </form>

      {error && <div className="mt-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="mt-6 space-y-6 rounded-3xl border border-slate-200 bg-slate-50 p-6">
          <div>
            <h4 className="text-lg font-semibold text-slate-900">Extracted Fields</h4>
            <p className="text-sm text-slate-500">Values extracted by the OCR pipeline.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Name</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.name || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">PAN</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.pan || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Aadhaar</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.aadhaar || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">DOB</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.dob || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Gender</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.gender || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Mobile</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.mobile || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Salary</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.salary ?? 'N/A'}</p>
            </div>
            <div className="sm:col-span-2 rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Address</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted?.address || 'N/A'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Matched</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.matched ? 'Yes' : 'No'}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Fraud Flags</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.fraud_flags?.length ?? 0}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default OCRResultsPage
