import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h3 className="text-2xl font-semibold text-slate-900">Page not found</h3>
      <p className="mt-3 text-slate-600">The page you are looking for does not exist.</p>
      <Link to="/" className="mt-6 inline-flex rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-700">
        Return home
      </Link>
    </div>
  )
}

export default NotFoundPage
