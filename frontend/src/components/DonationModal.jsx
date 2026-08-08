import { useCallback, useState } from 'react'
import { ApiError, authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'
import { Button } from './Button.jsx'
import { Modal } from './Modal.jsx'

const VALID_AMOUNT = /^\d+(\.\d{1,2})?$/

function resultPresentation(status) {
  if (status === 'COMPLETED') return { label: 'Completed', className: 'bg-emerald-50 text-emerald-800' }
  if (status === 'FAILED') return { label: 'Failed', className: 'bg-rose-50 text-rose-800' }
  return { label: 'Pending', className: 'bg-amber-50 text-amber-800' }
}

export function DonationModal({ recipeId, recipeTitle }) {
  const [isOpen, setIsOpen] = useState(false)
  const [amount, setAmount] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const close = useCallback(() => {
    if (isSubmitting) return
    setIsOpen(false)
    setAmount('')
    setError('')
    setResult(null)
  }, [isSubmitting])

  const submitDonation = async (event) => {
    event.preventDefault()
    const normalizedAmount = amount.trim()
    if (!VALID_AMOUNT.test(normalizedAmount) || Number(normalizedAmount) <= 0) {
      setError('Enter a positive amount with no more than 2 decimal places.')
      return
    }
    setIsSubmitting(true)
    setError('')
    try {
      const donation = await authenticatedApi.post(`/recipes/${recipeId}/donations`, { amount: normalizedAmount, currency: 'EUR' })
      setResult(donation)
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.data?.donation) setResult(requestError.data.donation)
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  const presentation = result ? resultPresentation(result.status) : null

  return (
    <>
      <Button type="button" onClick={() => setIsOpen(true)}>Donate</Button>
      <Modal isOpen={isOpen} onClose={close} title={`Support ${recipeTitle}`}>
        <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm leading-6 text-sky-900">Payments currently use the provider abstraction/test flow. A real Wise transfer is unavailable until the backend Wise integration is completed and configured.</p>
        {result ? <div className={`mt-5 rounded-2xl px-5 py-4 ${presentation.className}`}><p className="text-sm font-semibold">Donation result</p><p className="mt-1 text-xl font-black">{presentation.label}</p><p className="mt-1 text-sm">{result.amount} {result.currency}</p></div> : null}
        {error ? <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}
        {!result ? <form onSubmit={submitDonation} className="mt-5 space-y-5"><label htmlFor="donation-amount" className="block"><span className="text-sm font-semibold text-stone-800">Amount</span><div className="mt-2 flex rounded-xl border border-stone-300 bg-white focus-within:border-emerald-600 focus-within:ring-4 focus-within:ring-emerald-100"><input id="donation-amount" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="10.00" className="min-w-0 flex-1 rounded-l-xl px-4 py-3 outline-none" /><span className="grid place-items-center border-l border-stone-200 px-4 font-semibold text-stone-600">EUR</span></div></label><div className="flex justify-end gap-3"><Button type="button" variant="secondary" onClick={close}>Cancel</Button><Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Submitting...' : 'Confirm donation'}</Button></div></form> : <div className="mt-5 flex justify-end"><Button type="button" variant="secondary" onClick={close}>Close</Button></div>}
      </Modal>
    </>
  )
}
