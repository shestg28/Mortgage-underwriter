import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleLogin = async (event) => {
    event.preventDefault()
    setError(null)

    try {
      const data = new URLSearchParams()
      data.append('username', username)
      data.append('password', password)

      const response = await client.post('/api/auth/login', data, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      login(response.data.access_token)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check credentials.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <h1 className="text-2xl font-semibold text-slate-900 mb-6">Login</h1>
        {error && <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div>}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-indigo-500"
              placeholder="Enter your username"
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
              placeholder="Enter your password"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
          >
            Sign In
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-500">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="font-semibold text-indigo-600 hover:text-indigo-700">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
