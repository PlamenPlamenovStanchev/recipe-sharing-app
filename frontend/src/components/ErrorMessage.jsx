export function ErrorMessage({ message, onRetry }) {
  return (
    <div role="alert" className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-rose-900">
      <p className="font-semibold">We could not load this right now.</p>
      <p className="mt-1 text-sm text-rose-800">{message}</p>
      {onRetry ? <button type="button" onClick={onRetry} className="mt-4 rounded-full border border-rose-300 bg-white px-4 py-2 text-sm font-semibold text-rose-800 hover:bg-rose-100">Try again</button> : null}
    </div>
  )
}
