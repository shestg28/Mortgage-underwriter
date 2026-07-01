import { useState } from 'react'
import client from '../api/client'

function AnalyzeApplicationPage() {
  const [applicationId, setApplicationId] = useState('')
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!applicationId.trim()) {
      setError('Application ID is required.')
      return
    }
    if (!file) {
      setError('Select a PDF file to analyze.')
      return
    }

    try {
      setLoading(true)
      const formData = new FormData()
      formData.append('file', file)

      const response = await client.post(`/api/applications/${encodeURIComponent(applicationId.trim())}/analyzeWorkflow`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analyze workflow failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Analyze Application</h3>
      <form onSubmit={handleSubmit} className="grid gap-4">
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

        <div>
          <label className="block text-sm font-medium text-slate-700">PDF Document</label>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="mt-1 w-full text-sm text-slate-700"
          />
        </div>

        <button
          type="submit"
          className="rounded-xl w-auto max-w-[10rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          {loading ? 'Analyzing...' : 'Run Analyze Workflow'}
        </button>
      </form>

      {error && <div className="mt-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="mt-6 space-y-6 rounded-3xl border border-slate-200 bg-slate-50 p-6">
          <div>
            <h4 className="text-lg font-semibold text-slate-900">Analysis Result</h4>
            <p className="text-sm text-slate-500">Result from analyze workflow endpoint.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Decision</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.decision}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Risk Score</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.risk_score}</p>
            </div>
            <div className="sm:col-span-2 rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Matched</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.match ? 'Yes' : 'No'}</p>
            </div>
            <div className="sm:col-span-2 rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Extracted Name</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{result.extracted_fields?.name || 'N/A'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalyzeApplicationPage
