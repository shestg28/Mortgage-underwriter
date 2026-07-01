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

    if (!fullName || !dateOfBirth || !pan) {
      setError('Full name, date of birth, and PAN are required.')
      return
    }

    try {
      const response = await client.post('/api/customers/', {
        full_name: fullName,
        date_of_birth: dateOfBirth,
        pan,
        aadhaar,
        salary: salary ? parseFloat(salary) : undefined,
        address,
      })
      const generatedId = response.data.customer_id
      localStorage.setItem('customer_id', generatedId)
      setSuccess(`Customer saved successfully. Customer ID: ${generatedId}`)
      setCustomerId(generatedId)
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
    <div className="w-full rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-3xl font-semibold text-slate-900 mb-6">Create Customer</h3>
      {error && <div className="mb-5 rounded bg-red-100 px-5 py-4 text-base text-red-700">{error}</div>}
      {success && <div className="mb-5 rounded bg-emerald-100 px-5 py-4 text-base text-emerald-700">{success}</div>}
      <form className="space-y-8" onSubmit={handleSubmit}>
        <div className="flex items-center gap-6">
          <label className="w-40 text-base font-medium text-slate-700">Customer Number</label>
          <input
            value={customerId}
            placeholder="Auto-generated on save"
            className="w-[74ch] rounded-2xl border border-slate-300 bg-slate-100 px-5 py-4 text-base text-slate-500 outline-none focus:border-indigo-500"
            readOnly
            disabled
          />
        </div>
        <div className="flex items-center gap-6">
          <label className="w-40 text-base font-medium text-slate-700">Full Name</label>
          <input
            tabIndex={2}
            size={30}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-[74ch] rounded-2xl border border-slate-300 px-5 py-4 text-base outline-none focus:border-indigo-500"
            required
          />
        </div>
        <div className="flex items-center gap-6">
          <label className="w-40 text-base font-medium text-slate-700">Date of Birth</label>
          <input
            tabIndex={3}
            type="date"
            value={dateOfBirth}
            onChange={(e) => setDateOfBirth(e.target.value)}
            className="w-[74ch] rounded-2xl border border-slate-300 px-5 py-4 text-base outline-none focus:border-indigo-500"
            required
          />
        </div>
        <div className="flex items-center gap-6">
          <label className="w-40 text-base font-medium text-slate-700">PAN</label>
          <input
            tabIndex={4}
            size={10}
            maxLength={10}
            value={pan}
            onChange={(e) => setPan(e.target.value.toUpperCase())}
            className="w-[74ch] rounded-2xl border border-slate-300 px-5 py-4 text-base outline-none focus:border-indigo-500"
            placeholder="ABCDE1234F"
            required
          />
        </div>
        <div className="flex items-center gap-6">
          <label className="w-40 text-base font-medium text-slate-700">Aadhaar</label>
          <input
            tabIndex={5}
            size={16}
            maxLength={16}
            value={aadhaar}
            onChange={(e) => setAadhaar(e.target.value)}
            className="w-[74ch] rounded-2xl border border-slate-300 px-5 py-4 text-base outline-none focus:border-indigo-500"
          />
        </div>
        <div className="flex items-center gap-6">
          <label className="w-40 text-base font-medium text-slate-700">Salary</label>
          <input
            tabIndex={6}
            type="number"
            value={salary}
            onChange={(e) => setSalary(e.target.value)}
            className="w-[74ch] rounded-2xl border border-slate-300 px-5 py-4 text-base outline-none focus:border-indigo-500"
            min="0"
          />
        </div>
        <div className="flex items-start gap-6">
          <label className="w-40 pt-3 text-base font-medium text-slate-700">Address</label>
          <textarea
            tabIndex={7}
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-[74ch] rounded-2xl border border-slate-300 px-5 py-4 text-base outline-none focus:border-indigo-500"
            rows="6"
          />
        </div>
        <div>
          <button
            type="submit"
            className="rounded-xl w-auto max-w-[10rem] bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            Create Customer
          </button>
        </div>
      </form>
    </div>
  )
}

export default CustomerRegistrationPage
