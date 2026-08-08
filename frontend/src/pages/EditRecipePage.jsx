import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { useAuth } from '../auth/useAuth.js'
import { EmptyState } from '../components/EmptyState.jsx'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { LoadingSpinner } from '../components/LoadingSpinner.jsx'
import { RecipeForm } from '../components/RecipeForm.jsx'
import { RecipeImageUpload } from '../components/RecipeImageUpload.jsx'
import { authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

function canManageRecipe(recipe, user) {
  if (!recipe || !user) return false
  if (['MODERATOR', 'ADMIN'].includes(user.role)) return true
  return recipe.author?.id === user.id && ['DRAFT', 'REJECTED'].includes(recipe.status)
}

export function EditRecipePage() {
  const { recipeId } = useParams()
  const { currentUser } = useAuth()
  const [recipe, setRecipe] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isSubmittingForReview, setIsSubmittingForReview] = useState(false)

  useEffect(() => {
    let active = true
    async function loadRecipe() {
      setIsLoading(true)
      try {
        const data = await authenticatedApi.get(`/recipes/${recipeId}`)
        if (active) setRecipe(data)
      } catch (requestError) {
        if (active) setError(getRequestErrorMessage(requestError))
      } finally {
        if (active) setIsLoading(false)
      }
    }
    loadRecipe()
    return () => { active = false }
  }, [recipeId])

  const saveRecipe = async (recipeData) => {
    setIsSaving(true)
    setError('')
    setSuccess('')
    try {
      const updatedRecipe = await authenticatedApi.put(`/recipes/${recipeId}`, recipeData)
      setRecipe(updatedRecipe)
      setSuccess('Recipe saved.')
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSaving(false)
    }
  }

  const submitForReview = async () => {
    if (!window.confirm('Submit this recipe for moderator review? You will not be able to edit it while it is pending.')) return
    setIsSubmittingForReview(true)
    setError('')
    setSuccess('')
    try {
      const updatedRecipe = await authenticatedApi.post(`/recipes/${recipeId}/submit`)
      setRecipe(updatedRecipe)
      setSuccess('Recipe submitted for review.')
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSubmittingForReview(false)
    }
  }

  if (isLoading) return <LoadingSpinner label="Loading recipe..." />
  if (error && !recipe) return <section className="mx-auto max-w-4xl px-4 py-12"><ErrorMessage message={error} /></section>
  if (!recipe) return <section className="mx-auto max-w-4xl px-4 py-12"><EmptyState title="Recipe not found" message="This recipe is no longer available." action={<Link to="/recipes">Browse recipes</Link>} /></section>

  const mayManage = canManageRecipe(recipe, currentUser)
  const maySubmit = recipe.author?.id === currentUser?.id && ['DRAFT', 'REJECTED'].includes(recipe.status)
  if (!mayManage) return <section className="mx-auto max-w-4xl px-4 py-12"><EmptyState title="Editing is unavailable" message="Only the recipe owner can edit drafts or rejected recipes. Moderators and administrators can edit any recipe." action={<Link to={`/recipes/${recipe.id}`}>View recipe</Link>} /></section>

  return (
    <section className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm font-bold uppercase tracking-widest text-emerald-700">Recipe editor</p><h1 className="mt-3 text-4xl font-black tracking-tight text-stone-950">Edit recipe</h1><p className="mt-2 text-stone-600">Current status: <span className="font-semibold text-stone-900">{recipe.status}</span></p></div><Link to={`/recipes/${recipe.id}`} className="rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-800 hover:bg-stone-100">View recipe</Link></div>
      {error ? <div className="mt-6"><ErrorMessage message={error} /></div> : null}
      {success ? <p role="status" className="mt-6 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{success}</p> : null}
      <div className="mt-8"><RecipeForm recipe={recipe} onSubmit={saveRecipe} isSubmitting={isSaving} submitLabel="Save changes" /></div>
      <div className="mt-8"><RecipeImageUpload recipe={recipe} onUploaded={(uploaded) => setRecipe((current) => ({ ...current, ...uploaded }))} /></div>
      {maySubmit ? <div className="mt-8 rounded-3xl border border-amber-200 bg-amber-50 p-6"><h2 className="text-xl font-bold text-stone-950">Ready for review?</h2><p className="mt-2 text-sm text-stone-700">Submitting sends this recipe to moderators and pauses owner editing until it is reviewed.</p><button type="button" onClick={submitForReview} disabled={isSubmittingForReview} className="mt-4 rounded-full bg-amber-500 px-5 py-2.5 text-sm font-semibold text-stone-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-60">{isSubmittingForReview ? 'Submitting...' : 'Submit for review'}</button></div> : null}
    </section>
  )
}
