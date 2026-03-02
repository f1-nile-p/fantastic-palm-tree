import { Routes, Route, Link, useLocation } from 'react-router-dom'
import OrderQueue from './pages/OrderQueue'
import OrderDetail from './pages/OrderDetail'
import MasterData from './pages/MasterData'
import { DocumentTextIcon, CircleStackIcon } from '@heroicons/react/24/outline'

function NavLink({ to, children }) {
  const { pathname } = useLocation()
  const active = pathname === to || (to !== '/' && pathname.startsWith(to))
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        active
          ? 'bg-indigo-700 text-white'
          : 'text-indigo-100 hover:bg-indigo-600 hover:text-white'
      }`}
    >
      {children}
    </Link>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-indigo-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <span className="text-white text-lg font-bold tracking-tight">
                📦 PO Pipeline
              </span>
            </div>
            <div className="flex items-center gap-2">
              <NavLink to="/">
                <DocumentTextIcon className="w-5 h-5" />
                Orders
              </NavLink>
              <NavLink to="/master-data">
                <CircleStackIcon className="w-5 h-5" />
                Master Data
              </NavLink>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<OrderQueue />} />
          <Route path="/orders/:id" element={<OrderDetail />} />
          <Route path="/master-data" element={<MasterData />} />
        </Routes>
      </main>
    </div>
  )
}
