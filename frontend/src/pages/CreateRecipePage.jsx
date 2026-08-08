import { useState } from 'react'
import { useNavigate } from 'react-router'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { RecipeForm } from '../components/RecipeForm.jsx'
import { authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

export function CreateRecipePage() {
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const createRecipe = async (recipeData) => {
    setIsSubmitting(true)
    setError('')
    try {
      const recipe = await authenticatedApi.post('/recipes', recipeData)
      navigate(`/recipes/${recipe.id}/edit`, { replace: true })
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">Your kitchen</p>
      <h1 className="mt-3 text-4xl font-black tracking-tight text-stone-950">Create a recipe</h1>
      <p className="mt-2 text-stone-600">Save a complete recipe as a draft, then add its image and submit it for review.</p>
      <div className="mt-8">{error ? <div className="mb-6"><ErrorMessage message={error} /></div> : null}<RecipeForm onSubmit={createRecipe} isSubmitting={isSubmitting} submitLabel="Create draft" /></div>
    </section>
  )
}
