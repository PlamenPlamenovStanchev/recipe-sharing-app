import { Link, NavLink } from 'react-router'

const navLinkClass = ({ isActive }) =>
  `rounded-full px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? 'bg-emerald-100 text-emerald-800'
      : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950'
  }`

export function Navbar() {
  return (
    <header className="border-b border-stone-200 bg-white/90 backdrop-blur">
      <nav
        aria-label="Main navigation"
        className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8"
      >
        <Link
          to="/"
          className="flex items-center gap-2 text-lg font-bold tracking-tight text-stone-950"
        >
          <span
            aria-hidden="true"
            className="grid size-9 place-items-center rounded-xl bg-emerald-600 text-white"
          >
            R
          </span>
          Recipe Share
        </Link>
        <div className="flex flex-wrap items-center justify-end gap-1">
          <NavLink to="/" end className={navLinkClass}>Home</NavLink>
          <NavLink to="/recipes" className={navLinkClass}>Recipes</NavLink>
          <NavLink to="/login" className={navLinkClass}>Log in</NavLink>
          <Link
            to="/register"
            className="ml-1 rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-700"
          >
            Register
          </Link>
        </div>
      </nav>
    </header>
  )
}
