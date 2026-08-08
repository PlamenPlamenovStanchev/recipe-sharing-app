const statusStyles = {
  APPROVED: 'bg-emerald-100 text-emerald-800',
  PENDING: 'bg-amber-100 text-amber-800',
  DRAFT: 'bg-stone-100 text-stone-700',
  REJECTED: 'bg-rose-100 text-rose-800',
}

export function StatusBadge({ status }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${statusStyles[status] || 'bg-stone-100 text-stone-700'}`}>{status}</span>
}
