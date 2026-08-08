import { useEffect, useState } from 'react'
import { EmptyState } from '../components/EmptyState.jsx'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { LoadingSpinner } from '../components/LoadingSpinner.jsx'
import { RecipeCard } from '../components/RecipeCard.jsx'
import { api } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

export function RecipesPage() {
  const [recipes, setRecipes] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let isActive = true

    async function loadRecipes() {
      setIsLoading(true)
      setError('')
      try {
        const data = await api.get('/recipes')
        if (isActive) setRecipes(data)
      } catch (requestError) {
        if (isActive) setError(getRequestErrorMessage(requestError))
      } finally {
        if (isActive) setIsLoading(false)
      }
    }

    loadRecipes()
    return () => { isActive = false }
  }, [reloadKey])

  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">Recipes</p>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-stone-950">Community recipes</h1>
          <p className="mt-2 text-stone-600">Freshly shared dishes from the Recipe Share community.</p>
        </div>
        {!isLoading && !error ? <p className="rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-semibold text-emerald-800">{recipes.length} {recipes.length === 1 ? 'recipe' : 'recipes'}</p> : null}
      </div>
      <div className="mt-8">
        {isLoading ? <LoadingSpinner label="Loading recipes…" /> : null}
        {error ? <ErrorMessage message={error} onRetry={() => setReloadKey((value) => value + 1)} /> : null}
        {!isLoading && !error && recipes.length === 0 ? <EmptyState title="No recipes yet" message="The community cookbook is waiting for its first shared dish." /> : null}
        {!isLoading && !error && recipes.length > 0 ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{recipes.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} />)}</div> : null}
      </div>
    </section>
  )
}
