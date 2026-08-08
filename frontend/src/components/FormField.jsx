export function FormField({ label, error, id, ...inputProps }) {
  return (
    <label className="block" htmlFor={id}>
      <span className="text-sm font-semibold text-stone-800">{label}</span>
      <input
        id={id}
        className={`mt-2 block w-full rounded-xl border bg-white px-4 py-3 text-stone-950 outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 ${
          error ? 'border-rose-500' : 'border-stone-300'
        }`}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...inputProps}
      />
      {error ? <span id={`${id}-error`} className="mt-1 block text-sm text-rose-700">{error}</span> : null}
    </label>
  )
}
