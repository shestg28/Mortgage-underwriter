import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'

function RegisterPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('loan_officer')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const navigate = useNavigate()

  const handleRegister = async (event) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    if (!username.trim() || password.length < 6) {
      setError('Username is required and password must be at least 6 characters.')
      return
    }

    try {
      await client.post('/api/auth/register', {
        username,
        password,
        role,
      })

      const data = new URLSearchParams()
      data.append('username', username)
      data.append('password', password)

      const loginResponse = await client.post('/api/auth/login', data, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      localStorage.setItem('token', loginResponse.data.access_token)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Try again.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <h1 className="text-2xl font-semibold text-slate-900 mb-6">Register</h1>
        {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
        {success && <div className="mb-4 rounded bg-green-100 px-4 py-3 text-sm text-green-700">{success}</div>}
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-indigo-500"
              placeholder="Choose a username"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-indigo-500"
              placeholder="Create a password"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-indigo-500"
            >
              <option value="loan_officer">Loan Officer</option>
              <option value="underwriter">Underwriter</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
          >
            Register
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-indigo-600 hover:text-indigo-700">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
