import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function DashboardLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="flex min-h-screen">
        <aside className="w-72 bg-white border-r border-slate-200 p-6">
          <div className="mb-10">
            <h1 className="text-2xl font-bold text-slate-900">Speckit</h1>
            <p className="mt-2 text-sm text-slate-500">Mortgage underwriting dashboard</p>
          </div>
          <nav className="space-y-2 text-sm font-medium text-slate-700">
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/customers/register">Customer Registry</Link>
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/customers/search">Customer Search</Link>
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/applications">Loan Applications</Link>
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/upload">Document Upload</Link>
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/ocr-results">OCR Results</Link>
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/fraud-analysis">Fraud Analysis</Link>
            <Link className="block rounded-xl px-4 py-3 hover:bg-slate-100" to="/decision-results">Decision Results</Link>
          </nav>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-8 w-full rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white hover:bg-red-700"
          >
            Logout
          </button>
        </aside>
        <main className="flex-1 p-8">
          <header className="mb-8 flex items-center justify-between rounded-3xl bg-white px-6 py-5 shadow-sm">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Dashboard</h2>
              <p className="text-sm text-slate-500">Manage customers, applications, document processing, and fraud review.</p>
            </div>
          </header>
          <div className="space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
