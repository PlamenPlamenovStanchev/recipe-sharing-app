export function LoadingSpinner({ label = 'Loading…' }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 text-stone-600" role="status">
      <span aria-hidden="true" className="size-8 animate-spin rounded-full border-4 border-emerald-100 border-t-emerald-600" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}
