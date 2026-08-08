import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './useAuth.js'

export function ProtectedRoute() {
  const { isAuthenticated, isRestoring } = useAuth()
  const location = useLocation()

  if (isRestoring) {
    return <p className="p-8 text-center text-stone-600">Restoring your session…</p>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
