import { useState } from 'react'
import client from '../api/client'

function LoanApplicationPage() {
  const [customerId, setCustomerId] = useState('')
  const [applicationId, setApplicationId] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    setStatus('')
    setApplicationId('')

    if (!customerId.trim()) {
      setError('Customer ID is required to create an application.')
      return
    }

    try {
      setStatus('Creating application...')
      const response = await client.post('/api/applications/', null, {
        params: {
          customer_id: customerId.trim(),
        },
      })

      setApplicationId(response.data.application_id)
      setStatus(response.data.status || 'created')
      setSuccess('Application created successfully.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Application creation failed.')
      setStatus('')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Create Loan Application</h3>
      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mb-4 rounded bg-emerald-100 px-4 py-3 text-sm text-emerald-700">{success}</div>}
      <form onSubmit={handleSubmit} className="grid gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Customer ID</label>
          <input
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            placeholder="Enter existing customer ID"
            className="mt-1 w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            required
          />
        </div>
        <button
          type="submit"
          className="rounded-xl w-auto max-w-[10rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Create Application
        </button>
      </form>
      {applicationId && (
        <div className="mt-8 rounded-2xl bg-slate-50 p-6 shadow-sm">
          <p className="text-sm text-slate-500">Application ID</p>
          <p className="mt-2 text-lg font-semibold text-slate-900">{applicationId}</p>
          <p className="mt-1 text-sm text-slate-600">Status: {status}</p>
        </div>
      )}
    </div>
  )
}

export default LoanApplicationPage
