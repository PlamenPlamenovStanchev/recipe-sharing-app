import { Navigate, Outlet } from 'react-router'
import { useAuth } from './useAuth.js'

export function RoleRoute({ allowedRoles }) {
  const { currentUser, isAuthenticated, isRestoring } = useAuth()

  if (isRestoring) {
    return <p className="p-8 text-center text-stone-600">Restoring your session…</p>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!allowedRoles.includes(currentUser?.role)) {
    // This only improves navigation; the backend enforces authorization.
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
