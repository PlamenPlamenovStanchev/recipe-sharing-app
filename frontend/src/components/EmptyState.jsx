export function EmptyState({ title, message, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-stone-300 bg-white p-10 text-center">
      <div aria-hidden="true" className="mx-auto grid size-12 place-items-center rounded-2xl bg-emerald-100 text-xl font-bold text-emerald-700">R</div>
      <h2 className="mt-4 text-xl font-bold text-stone-950">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-stone-600">{message}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}
