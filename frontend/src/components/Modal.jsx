import { useEffect } from 'react'

export function Modal({ isOpen, title, children, onClose }) {
  useEffect(() => {
    if (!isOpen) return undefined
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-stone-950/60 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <section role="dialog" aria-modal="true" aria-labelledby="modal-title" className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl sm:p-8">
        <div className="flex items-start justify-between gap-4"><h2 id="modal-title" className="text-2xl font-black tracking-tight text-stone-950">{title}</h2><button type="button" onClick={onClose} aria-label="Close dialog" className="grid size-9 place-items-center rounded-full bg-stone-100 text-xl text-stone-700 hover:bg-stone-200">×</button></div>
        <div className="mt-5">{children}</div>
      </section>
    </div>
  )
}
