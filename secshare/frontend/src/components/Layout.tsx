import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { Shield, LogOut, CreditCard } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <Shield className="w-8 h-8 text-primary-600" />
                <span className="text-xl font-semibold text-gray-900">SecShare</span>
              </Link>
              <div className="ml-10 flex space-x-4">
                <Link
                  to="/"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/create"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Create Secret
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <Link
                to="/billing"
                className="text-gray-700 hover:text-gray-900"
                title="Billing"
              >
                <CreditCard className="w-5 h-5" />
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-700 hover:text-gray-900"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
