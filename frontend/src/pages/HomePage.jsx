import { Link } from 'react-router'

export function HomePage() {
  return (
    <section className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-center lg:px-8 lg:py-28">
      <div>
        <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-emerald-700">Cook · Share · Discover</p>
        <h1 className="max-w-3xl text-5xl font-black tracking-tight text-stone-950 sm:text-6xl">Good recipes are meant to be shared.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-600">Discover community recipes and keep your own kitchen favourites in one welcoming place.</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/recipes" className="rounded-full bg-emerald-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-emerald-700">Browse recipes</Link>
          <Link to="/register" className="rounded-full border border-stone-300 bg-white px-6 py-3 font-semibold text-stone-800 transition-colors hover:bg-stone-100">Join the community</Link>
        </div>
      </div>
      <div className="rounded-[2rem] bg-emerald-950 p-8 text-white shadow-xl shadow-emerald-950/10 sm:p-10">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-300">Coming together</p>
        <h2 className="mt-4 text-3xl font-bold">A growing community cookbook</h2>
        <p className="mt-4 leading-7 text-emerald-100">Recipe browsing, sharing, comments, likes, images, and donations will be connected here in the next UI phases.</p>
      </div>
    </section>
  )
}
