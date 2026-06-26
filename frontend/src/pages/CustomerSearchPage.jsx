import { useState } from 'react'
import client from '../api/client'

function CustomerSearchPage() {
  const [customerId, setCustomerId] = useState('')
  const [customer, setCustomer] = useState(null)
  const [error, setError] = useState(null)

  const handleSearch = async (event) => {
    event.preventDefault()
    setError(null)
    setCustomer(null)

    if (!customerId.trim()) {
      setError('Enter a customer ID to search.')
      return
    }

    try {
      const response = await client.get(`/api/customers/lookup/${encodeURIComponent(customerId)}`)
      setCustomer(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Customer lookup failed.')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Search Customer</h3>
      <form onSubmit={handleSearch} className="mb-6 flex flex-col gap-4 sm:flex-row">
        <input
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          placeholder="Customer ID"
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
        />
        <button type="submit" className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-700">
          Search
        </button>
      </form>
      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {customer && (
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-6">
          <div>
            <h4 className="text-lg font-semibold text-slate-900">Customer Details</h4>
            <p className="text-sm text-slate-500">Information retrieved from backend lookup.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Customer ID</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.customer_id}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Full Name</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.full_name}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Date of Birth</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.date_of_birth}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">PAN</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.pan}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Aadhaar</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.aadhaar}</p>
            </div>
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Salary</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.salary ?? 'N/A'}</p>
            </div>
            <div className="sm:col-span-2 rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Address</p>
              <p className="mt-1 text-base font-semibold text-slate-900">{customer.address || 'N/A'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CustomerSearchPage
