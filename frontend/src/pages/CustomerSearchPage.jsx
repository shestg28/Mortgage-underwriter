import { useState, useEffect, useRef } from 'react'
import client from '../api/client'

function CustomerSearchPage() {
  const [prefix, setPrefix] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [selectedCustomerId, setSelectedCustomerId] = useState(localStorage.getItem('customer_id') || '')
  const debounceRef = useRef(null)

  const fetchResults = async (searchPrefix) => {
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      const response = await client.get('/api/customers/search', {
        params: { prefix: searchPrefix },
      })
      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Customer search failed.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    const trimmed = prefix.trim()
    if (!trimmed) {
      setResults([])
      setError(null)
      setLoading(false)
      return
    }

    debounceRef.current = setTimeout(() => {
      fetchResults(trimmed)
    }, 300)

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [prefix])

  const handleSearch = async (event) => {
    event.preventDefault()
    const trimmed = prefix.trim()
    if (!trimmed) {
      setError('Enter a customer prefix to search.')
      return
    }
    await fetchResults(trimmed)
  }

  const handleRowClick = (customerId) => {
    localStorage.setItem('customer_id', customerId)
    setSelectedCustomerId(customerId)
    setSuccess(`Selected customer ${customerId} for future workflows.`)
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Search Customer</h3>
      <form onSubmit={handleSearch} className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
        <input
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="Customer ID prefix"
          className="w-full max-w-xl rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
        />
        <button type="submit" className="rounded-xl w-auto max-w-[8rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
          Search
        </button>
      </form>

      {loading && <div className="mb-4 text-sm text-slate-600">Searching customers...</div>}
      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mb-4 rounded bg-emerald-100 px-4 py-3 text-sm text-emerald-700">{success}</div>}

      {selectedCustomerId && (
        <div className="mb-6 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
          Selected Customer ID: <span className="font-semibold">{selectedCustomerId}</span>
        </div>
      )}

      {!loading && results.length === 0 && !error && prefix.trim() && (
        <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-600">No matching customers found.</div>
      )}

      {results.length > 0 && (
        <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <table className="min-w-full text-left text-sm text-slate-700">
            <thead>
              <tr>
                <th className="border-b px-4 py-3 font-semibold">Customer ID</th>
                <th className="border-b px-4 py-3 font-semibold">Full Name</th>
                <th className="border-b px-4 py-3 font-semibold">PAN</th>
                <th className="border-b px-4 py-3 font-semibold">Salary</th>
              </tr>
            </thead>
            <tbody>
              {results.map((customer) => (
                <tr
                  key={customer.customer_id}
                  onClick={() => handleRowClick(customer.customer_id)}
                  className={`cursor-pointer hover:bg-slate-100 ${selectedCustomerId === customer.customer_id ? 'bg-slate-100' : ''}`}
                >
                  <td className="border-b px-4 py-3">{customer.customer_id}</td>
                  <td className="border-b px-4 py-3">{customer.full_name}</td>
                  <td className="border-b px-4 py-3">{customer.pan}</td>
                  <td className="border-b px-4 py-3">{customer.salary ?? 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default CustomerSearchPage
