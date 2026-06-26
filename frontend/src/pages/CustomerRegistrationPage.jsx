import { useState } from 'react'
import client from '../api/client'

function CustomerRegistrationPage() {
  const [customerId, setCustomerId] = useState('')
  const [fullName, setFullName] = useState('')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [pan, setPan] = useState('')
  const [aadhaar, setAadhaar] = useState('')
  const [salary, setSalary] = useState('')
  const [address, setAddress] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    if (!customerId || !fullName || !dateOfBirth || !pan) {
      setError('Customer ID, full name, date of birth, and PAN are required.')
      return
    }

    try {
      await client.post('/api/customers/', {
        customer_id: customerId,
        full_name: fullName,
        date_of_birth: dateOfBirth,
        pan,
        aadhaar,
        salary: salary ? parseFloat(salary) : undefined,
        address,
      })
      setSuccess('Customer created successfully.')
      setCustomerId('')
      setFullName('')
      setDateOfBirth('')
      setPan('')
      setAadhaar('')
      setSalary('')
      setAddress('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Customer creation failed.')
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900 mb-6">Create Customer</h3>
      {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mb-4 rounded bg-emerald-100 px-4 py-3 text-sm text-emerald-700">{success}</div>}
      <form className="grid gap-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm font-medium text-slate-700">Customer ID</label>
          <input
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Full Name</label>
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Date of Birth</label>
          <input
            type="date"
            value={dateOfBirth}
            onChange={(e) => setDateOfBirth(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">PAN</label>
          <input
            value={pan}
            onChange={(e) => setPan(e.target.value.toUpperCase())}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            placeholder="ABCDE1234F"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Aadhaar</label>
          <input
            value={aadhaar}
            onChange={(e) => setAadhaar(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Salary</label>
          <input
            type="number"
            value={salary}
            onChange={(e) => setSalary(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            min="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Address</label>
          <textarea
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-indigo-500"
            rows="3"
          />
        </div>
        <button type="submit" className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-700">
          Create Customer
        </button>
      </form>
    </div>
  )
}

export default CustomerRegistrationPage
