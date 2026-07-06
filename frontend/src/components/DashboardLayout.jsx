import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function DashboardLayout() {
  const { logout, role } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const showHeader = location.pathname === '/'
  const isCustomer = role === 'customer'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen w-screen bg-slate-100">
      <div className="flex min-h-screen w-full">
        <aside className="w-96 min-w-[24rem] bg-white border-r border-slate-200 p-8">
          <nav className="space-y-4 text-base font-semibold text-slate-700">
            <div className="mb-4 rounded-2xl bg-slate-100 px-5 py-4 text-sm font-semibold text-slate-900">Mortgage Intelligence Layer</div>
            {isCustomer ? (
              <>
                <Link className="block rounded-2xl px-5 py-4 hover:bg-slate-100" to="/customers/register">Customer Registry</Link>
                <Link className="block rounded-2xl px-5 py-4 hover:bg-slate-100" to="/upload">Document Upload</Link>
              </>
            ) : (
              <>
                <Link className="block rounded-2xl px-5 py-4 hover:bg-slate-100" to="/customers/search">Customer Search</Link>
                <Link className="block rounded-2xl px-5 py-4 hover:bg-slate-100" to="/applications">Pending Applications</Link>
                <Link className="block rounded-2xl px-5 py-4 hover:bg-slate-100" to="/applications/approved">Approved Applications</Link>
                <Link className="block rounded-2xl px-5 py-4 hover:bg-slate-100" to="/applications/rejected">Rejected Applications</Link>
              </>
            )}
          </nav>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-10 w-full rounded-2xl bg-red-600 px-5 py-4 text-base font-semibold text-white hover:bg-red-700"
          >
            Logout
          </button>
        </aside>
        <main className="flex-1 min-w-0 p-8">
          {showHeader && (
            <header className="mb-10 flex items-center justify-between rounded-3xl bg-white px-8 py-6 shadow-sm">
              <div>
                <h2 className="text-2xl font-semibold text-slate-900">Dashboard</h2>
                <p className="text-base text-slate-500">Manage customers, applications, document processing, and fraud review.</p>
              </div>
            </header>
          )}
          <div className="space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
