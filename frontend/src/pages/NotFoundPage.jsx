import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <section className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">404</p>
      <h1 className="mt-3 text-4xl font-black tracking-tight text-stone-950">Page not found</h1>
      <Link to="/" className="mt-8 inline-block rounded-full bg-emerald-600 px-5 py-3 font-semibold text-white hover:bg-emerald-700">Return home</Link>
    </section>
  )
}
