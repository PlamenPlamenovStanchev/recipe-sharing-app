export function AuthCard({ eyebrow, title, children }) {
  return (
    <section className="mx-auto max-w-xl px-4 py-16 sm:px-6">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">{eyebrow}</p>
      <h1 className="mt-3 text-4xl font-black tracking-tight text-stone-950">{title}</h1>
      <div className="mt-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">{children}</div>
    </section>
  )
}
