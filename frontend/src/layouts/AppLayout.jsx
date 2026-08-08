import { Outlet } from 'react-router'
import { Navbar } from '../components/Navbar.jsx'

export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-stone-50 text-stone-900">
      <Navbar />
      <main className="flex-1"><Outlet /></main>
      <footer className="border-t border-stone-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-stone-500 sm:px-6 lg:px-8">
          Recipe Share · A place for recipes worth passing on.
        </div>
      </footer>
    </div>
  )
}
