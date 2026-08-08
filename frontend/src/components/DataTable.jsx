export function DataTable({ columns, rows, getRowKey, emptyMessage = 'No records available.' }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-stone-200">
      <table className="min-w-full divide-y divide-stone-200 text-left">
        <thead className="bg-stone-50">
          <tr>{columns.map((column) => <th key={column.key} scope="col" className={`whitespace-nowrap px-5 py-3 text-xs font-bold uppercase tracking-wide text-stone-500 ${column.headerClassName || ''}`}>{column.label}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-stone-100 bg-white">
          {rows.length === 0 ? <tr><td colSpan={columns.length} className="px-5 py-10 text-center text-sm text-stone-600">{emptyMessage}</td></tr> : rows.map((row) => <tr key={getRowKey(row)} className="align-middle">{columns.map((column) => <td key={column.key} className={`px-5 py-4 text-sm text-stone-700 ${column.className || ''}`}>{column.render ? column.render(row) : row[column.key]}</td>)}</tr>)}
        </tbody>
      </table>
    </div>
  )
}
