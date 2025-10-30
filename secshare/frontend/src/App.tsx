import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import CreateSecret from './pages/CreateSecret'
import ViewSecret from './pages/ViewSecret'
import Billing from './pages/Billing'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  return token ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/s/:secretId" element={<ViewSecret />} />

        <Route element={<Layout />}>
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/create"
            element={
              <PrivateRoute>
                <CreateSecret />
              </PrivateRoute>
            }
          />
          <Route
            path="/billing"
            element={
              <PrivateRoute>
                <Billing />
              </PrivateRoute>
            }
          />
        </Route>
      </Routes>
    </>
  )
}

export default App
