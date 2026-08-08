import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { Button } from '../components/Button.jsx'
import { EmptyState } from '../components/EmptyState.jsx'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { LoadingSpinner } from '../components/LoadingSpinner.jsx'
import { Modal } from '../components/Modal.jsx'
import { authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

function authorName(author) {
  return author?.username || [author?.first_name, author?.last_name].filter(Boolean).join(' ') || 'Recipe Share member'
}

function formatSubmittedAt(value) {
  if (!value) return 'Submission time unavailable'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function ModeratorPage() {
  const [recipes, setRecipes] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [actionRecipeId, setActionRecipeId] = useState(null)
  const [rejectingRecipe, setRejectingRecipe] = useState(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [error, setError] = useState('')
  const [modalError, setModalError] = useState('')
  const [feedback, setFeedback] = useState('')

  const loadPendingRecipes = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      setRecipes(await authenticatedApi.get('/recipes/pending'))
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadPendingRecipes() }, [loadPendingRecipes])

  const approveRecipe = async (recipe) => {
    if (!window.confirm(`Approve “${recipe.title}”? It will become publicly visible.`)) return
    setActionRecipeId(recipe.id)
    setError('')
    setFeedback('')
    try {
      await authenticatedApi.post(`/recipes/${recipe.id}/approve`)
      await loadPendingRecipes()
      setFeedback(`“${recipe.title}” was approved.`)
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setActionRecipeId(null)
    }
  }

  const openRejectModal = (recipe) => {
    setRejectingRecipe(recipe)
    setRejectionReason('')
    setModalError('')
  }

  const closeRejectModal = useCallback(() => {
    if (actionRecipeId) return
    setRejectingRecipe(null)
    setRejectionReason('')
    setModalError('')
  }, [actionRecipeId])

  const rejectRecipe = async (event) => {
    event.preventDefault()
    const reason = rejectionReason.trim()
    if (reason.length < 5 || reason.length > 500) {
      setModalError('Rejection reason must contain between 5 and 500 characters.')
      return
    }
    setActionRecipeId(rejectingRecipe.id)
    setModalError('')
    setFeedback('')
    try {
      await authenticatedApi.post(`/recipes/${rejectingRecipe.id}/reject`, { reason })
      const rejectedTitle = rejectingRecipe.title
      setRejectingRecipe(null)
      setRejectionReason('')
      await loadPendingRecipes()
      setFeedback(`“${rejectedTitle}” was rejected.`)
    } catch (requestError) {
      setModalError(getRequestErrorMessage(requestError))
    } finally {
      setActionRecipeId(null)
    }
  }

  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">Moderation</p>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-4xl font-black tracking-tight text-stone-950">Pending recipes</h1><p className="mt-2 text-stone-600">Review submissions in the order they entered the queue.</p></div>{!isLoading && !error ? <span className="rounded-full bg-amber-100 px-3 py-1.5 text-sm font-semibold text-amber-800">{recipes.length} pending</span> : null}</div>
      {feedback ? <p role="status" className="mt-6 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800">{feedback}</p> : null}
      {error ? <div className="mt-6"><ErrorMessage message={error} onRetry={loadPendingRecipes} /></div> : null}
      {isLoading ? <LoadingSpinner label="Loading moderation queue..." /> : null}
      {!isLoading && !error && recipes.length === 0 ? <div className="mt-8"><EmptyState title="Queue cleared" message="There are no recipes waiting for review." /></div> : null}
      {!isLoading && !error && recipes.length > 0 ? <div className="mt-8 overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm"><div className="hidden grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-4 border-b border-stone-200 bg-stone-50 px-6 py-3 text-xs font-bold uppercase tracking-wide text-stone-500 md:grid"><span>Recipe</span><span>Author</span><span>Submitted</span><span>Actions</span></div>{recipes.map((recipe) => <article key={recipe.id} className="grid gap-4 border-b border-stone-100 p-5 last:border-b-0 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1.2fr)_auto] md:items-center md:px-6"><div><h2 className="font-bold text-stone-950">{recipe.title}</h2><p className="mt-1 text-xs text-stone-500 md:hidden">Recipe submission</p></div><div><span className="text-xs font-semibold uppercase text-stone-500 md:hidden">Author: </span><span className="text-sm text-stone-700">{authorName(recipe.author)}</span></div><div><span className="text-xs font-semibold uppercase text-stone-500 md:hidden">Submitted: </span><span className="text-sm text-stone-700">{formatSubmittedAt(recipe.submitted_at)}</span></div><div className="flex flex-wrap gap-2 md:justify-end"><Link to={`/recipes/${recipe.id}`} className="rounded-full border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 hover:bg-stone-100">Open</Link><Button type="button" onClick={() => approveRecipe(recipe)} disabled={actionRecipeId === recipe.id}>Approve</Button><Button type="button" variant="danger" onClick={() => openRejectModal(recipe)} disabled={actionRecipeId === recipe.id}>Reject</Button></div></article>)}</div> : null}
      <Modal isOpen={Boolean(rejectingRecipe)} onClose={closeRejectModal} title={`Reject ${rejectingRecipe?.title || 'recipe'}`}><form onSubmit={rejectRecipe}><label htmlFor="rejection-reason" className="block"><span className="text-sm font-semibold text-stone-800">Reason</span><textarea id="rejection-reason" value={rejectionReason} onChange={(event) => setRejectionReason(event.target.value)} minLength="5" maxLength="500" rows="5" required className="mt-2 block w-full rounded-xl border border-stone-300 px-4 py-3 outline-none focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100" /></label><p className="mt-2 text-xs text-stone-500">{rejectionReason.trim().length}/500 characters</p>{modalError ? <p role="alert" className="mt-3 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{modalError}</p> : null}<div className="mt-5 flex justify-end gap-3"><Button type="button" variant="secondary" onClick={closeRejectModal}>Cancel</Button><Button type="submit" variant="danger" disabled={Boolean(actionRecipeId)}>{actionRecipeId ? 'Rejecting...' : 'Reject recipe'}</Button></div></form></Modal>
    </section>
  )
}
