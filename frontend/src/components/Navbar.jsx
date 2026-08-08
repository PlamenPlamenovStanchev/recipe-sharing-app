import { Link, NavLink, useNavigate } from 'react-router'
import { useAuth } from '../auth/useAuth.js'

const navLinkClass = ({ isActive }) =>
  `rounded-full px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? 'bg-emerald-100 text-emerald-800'
      : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950'
  }`

export function Navbar() {
  const { currentUser, isAuthenticated, isRestoring, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="border-b border-stone-200 bg-white/90 backdrop-blur">
      <nav aria-label="Main navigation" className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold tracking-tight text-stone-950">
          <span aria-hidden="true" className="grid size-9 place-items-center rounded-xl bg-emerald-600 text-white">R</span>
          Recipe Share
        </Link>
        <div className="flex flex-wrap items-center justify-end gap-1">
          <NavLink to="/" end className={navLinkClass}>Home</NavLink>
          <NavLink to="/recipes" className={navLinkClass}>Recipes</NavLink>
          {isRestoring ? null : isAuthenticated ? (
            <>
              <NavLink to="/recipes/new" className={navLinkClass}>Create Recipe</NavLink>
              {['MODERATOR', 'ADMIN'].includes(currentUser.role) ? <NavLink to="/moderator" className={navLinkClass}>Moderate</NavLink> : null}
              {currentUser.role === 'ADMIN' ? <NavLink to="/admin" className={navLinkClass}>Admin</NavLink> : null}
              <span className="hidden rounded-full bg-stone-100 px-3 py-2 text-right text-xs leading-tight text-stone-600 sm:block">
                <strong className="block text-sm text-stone-900">{currentUser.username}</strong>
                {currentUser.role}
              </span>
              <button type="button" onClick={handleLogout} className="ml-1 rounded-full border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 transition-colors hover:bg-stone-100">Logout</button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navLinkClass}>Log in</NavLink>
              <Link to="/register" className="ml-1 rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-700">Register</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
