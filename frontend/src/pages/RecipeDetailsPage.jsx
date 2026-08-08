import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { useAuth } from '../auth/useAuth.js'
import { CommentsSection } from '../components/CommentsSection.jsx'
import { DonationModal } from '../components/DonationModal.jsx'
import { EmptyState } from '../components/EmptyState.jsx'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { LoadingSpinner } from '../components/LoadingSpinner.jsx'
import { LikeButton } from '../components/LikeButton.jsx'
import { RecipeImage } from '../components/RecipeImage.jsx'
import { api, authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

function formatDate(value) {
  if (!value) return null
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'long' }).format(new Date(value))
}

function authorName(author) {
  return author?.username || [author?.first_name, author?.last_name].filter(Boolean).join(' ') || 'Recipe Share member'
}

function ingredientLabel(ingredient) {
  return [ingredient.quantity, ingredient.unit, ingredient.name].filter(Boolean).join(' ')
}

function canManageRecipe(recipe, user) {
  if (!recipe || !user) return false
  if (['MODERATOR', 'ADMIN'].includes(user.role)) return true
  return recipe.author?.id === user.id && ['DRAFT', 'REJECTED'].includes(recipe.status)
}

export function RecipeDetailsPage() {
  const { recipeId } = useParams()
  const { currentUser, isAuthenticated, isRestoring } = useAuth()
  const [recipe, setRecipe] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)
  const updateLikeCount = useCallback((likeCount) => {
    setRecipe((current) => current ? { ...current, like_count: likeCount } : current)
  }, [])

  useEffect(() => {
    if (isRestoring) return undefined
    let isActive = true

    async function loadRecipe() {
      setIsLoading(true)
      setError('')
      try {
        const client = isAuthenticated ? authenticatedApi : api
        const data = await client.get(`/recipes/${recipeId}`)
        if (isActive) setRecipe(data)
      } catch (requestError) {
        if (isActive) setError(getRequestErrorMessage(requestError))
      } finally {
        if (isActive) setIsLoading(false)
      }
    }

    loadRecipe()
    return () => { isActive = false }
  }, [isAuthenticated, isRestoring, recipeId, reloadKey])

  if (isRestoring || isLoading) return <LoadingSpinner label="Loading recipe…" />
  if (error) return <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"><ErrorMessage message={error} onRetry={() => setReloadKey((value) => value + 1)} /></section>
  if (!recipe) return <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8"><EmptyState title="Recipe not found" message="This recipe may have been removed or is not available to you." action={<Link to="/recipes" className="font-semibold text-emerald-700">Browse recipes</Link>} /></section>

  const createdAt = formatDate(recipe.created_at)
  const approvedAt = formatDate(recipe.approved_at)
  const mayManage = canManageRecipe(recipe, currentUser)
  const mayDonate = isAuthenticated && recipe.status === 'APPROVED' && recipe.author?.id !== currentUser?.id

  return (
    <article className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <div className="flex flex-wrap items-center justify-between gap-3"><Link to="/recipes" className="text-sm font-semibold text-emerald-700 hover:text-emerald-800">← Back to recipes</Link>{mayManage ? <Link to={`/recipes/${recipe.id}/edit`} className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">Edit recipe</Link> : null}</div>
      <div className="mt-6 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <RecipeImage recipe={recipe} className="aspect-4/3 w-full overflow-hidden rounded-3xl shadow-lg shadow-emerald-950/10" />
        <div>
          <div className="flex flex-wrap items-center gap-2">
            {recipe.status && recipe.status !== 'APPROVED' ? <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">{recipe.status}</span> : null}
            {recipe.status === 'APPROVED' ? <LikeButton recipeId={recipe.id} initialCount={recipe.like_count ?? 0} initiallyLiked={recipe.liked_by_current_user ?? false} isAuthenticated={isAuthenticated} onCountChange={updateLikeCount} /> : <span className="rounded-full bg-rose-50 px-3 py-1 text-sm font-semibold text-rose-700">{recipe.like_count ?? 0} likes</span>}
          </div>
          <h1 className="mt-4 text-4xl font-black tracking-tight text-stone-950 sm:text-5xl">{recipe.title}</h1>
          <p className="mt-4 text-lg leading-8 text-stone-600">{recipe.description}</p>
          <dl className="mt-7 grid gap-4 border-t border-stone-200 pt-6 text-sm sm:grid-cols-2">
            <div><dt className="font-semibold text-stone-500">Shared by</dt><dd className="mt-1 font-medium text-stone-900">{authorName(recipe.author)}</dd></div>
            {createdAt ? <div><dt className="font-semibold text-stone-500">Created</dt><dd className="mt-1 font-medium text-stone-900">{createdAt}</dd></div> : null}
            {approvedAt ? <div><dt className="font-semibold text-stone-500">Approved</dt><dd className="mt-1 font-medium text-stone-900">{approvedAt}</dd></div> : null}
          </dl>
          {mayDonate ? <div className="mt-7"><DonationModal recipeId={recipe.id} recipeTitle={recipe.title} /></div> : null}
        </div>
      </div>
      <div className="mt-12 grid gap-10 lg:grid-cols-2">
        <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-2xl font-bold tracking-tight text-stone-950">Ingredients</h2>
          {recipe.ingredients?.length ? <ul className="mt-5 space-y-3">{recipe.ingredients.map((ingredient, index) => <li key={`${ingredient.name}-${index}`} className="border-b border-stone-100 pb-3 text-stone-700"><span className="font-medium text-stone-900">{ingredientLabel(ingredient)}</span>{ingredient.notes ? <span className="block pt-1 text-sm text-stone-500">{ingredient.notes}</span> : null}</li>)}</ul> : <p className="mt-4 text-stone-600">Ingredients have not been added yet.</p>}
        </section>
        <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-2xl font-bold tracking-tight text-stone-950">Method</h2>
          {recipe.steps?.length ? <ol className="mt-5 space-y-5">{recipe.steps.map((step, index) => <li key={step.step_number ?? index} className="flex gap-4"><span className="grid size-7 shrink-0 place-items-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">{step.step_number ?? index + 1}</span><p className="pt-0.5 leading-7 text-stone-700">{step.instruction}</p></li>)}</ol> : <p className="mt-4 text-stone-600">Steps have not been added yet.</p>}
        </section>
      </div>
      {recipe.status === 'APPROVED' ? <CommentsSection recipeId={recipe.id} currentUser={currentUser} isAuthenticated={isAuthenticated} /> : null}
    </article>
  )
}
