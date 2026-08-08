import { useEffect, useState } from 'react'
import { FormField } from './FormField.jsx'

const emptyIngredient = () => ({ name: '', quantity: '', unit: '', notes: '' })
const emptyStep = () => ({ instruction: '' })

function recipeToForm(recipe) {
  return {
    title: recipe?.title || '',
    description: recipe?.description || '',
    ingredients: recipe?.ingredients?.map((ingredient) => ({
      name: ingredient.name || '', quantity: ingredient.quantity || '', unit: ingredient.unit || '', notes: ingredient.notes || '',
    })) || [emptyIngredient()],
    steps: recipe?.steps?.map((step) => ({ instruction: step.instruction || '' })) || [emptyStep()],
  }
}

function textAreaClass(error) {
  return `mt-2 block w-full rounded-xl border bg-white px-4 py-3 text-stone-950 outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 ${error ? 'border-rose-500' : 'border-stone-300'}`
}

export function RecipeForm({ recipe, onSubmit, isSubmitting, submitLabel }) {
  const [values, setValues] = useState(() => recipeToForm(recipe))
  const [error, setError] = useState('')

  useEffect(() => setValues(recipeToForm(recipe)), [recipe])

  const updateRecipeField = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.value }))
  const updateIngredient = (index, field, value) => setValues((current) => ({
    ...current,
    ingredients: current.ingredients.map((ingredient, itemIndex) => itemIndex === index ? { ...ingredient, [field]: value } : ingredient),
  }))
  const updateStep = (index, instruction) => setValues((current) => ({
    ...current,
    steps: current.steps.map((step, itemIndex) => itemIndex === index ? { ...step, instruction } : step),
  }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    const title = values.title.trim()
    const description = values.description.trim()
    const ingredients = values.ingredients.map((ingredient, index) => ({
      name: ingredient.name.trim(), quantity: ingredient.quantity.trim() || null, unit: ingredient.unit.trim() || null, notes: ingredient.notes.trim() || null, position: index + 1,
    }))
    const steps = values.steps.map((step, index) => ({ step_number: index + 1, instruction: step.instruction.trim() }))

    if (!title || !description || ingredients.some((ingredient) => !ingredient.name) || steps.some((step) => !step.instruction)) {
      setError('Add a title, description, every ingredient name, and every step instruction.')
      return
    }

    setError('')
    await onSubmit({ title, description, ingredients, steps })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {error ? <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}
      <div className="grid gap-5 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <FormField id="recipe-title" label="Title" name="title" value={values.title} onChange={updateRecipeField} maxLength="200" required />
        <label className="block" htmlFor="recipe-description"><span className="text-sm font-semibold text-stone-800">Description</span><textarea id="recipe-description" name="description" value={values.description} onChange={updateRecipeField} rows="5" required className={textAreaClass(false)} /></label>
      </div>

      <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-2xl font-bold text-stone-950">Ingredients</h2><p className="mt-1 text-sm text-stone-600">Use the row order as each ingredient position.</p></div><button type="button" onClick={() => setValues((current) => ({ ...current, ingredients: [...current.ingredients, emptyIngredient()] }))} className="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-100">+ Add ingredient</button></div>
        <div className="mt-6 space-y-5">{values.ingredients.map((ingredient, index) => <div key={index} className="rounded-2xl border border-stone-200 p-4"><div className="mb-4 flex items-center justify-between"><span className="font-semibold text-stone-800">Ingredient {index + 1}</span>{values.ingredients.length > 1 ? <button type="button" onClick={() => setValues((current) => ({ ...current, ingredients: current.ingredients.filter((_, itemIndex) => itemIndex !== index) }))} className="text-sm font-semibold text-rose-700 hover:text-rose-900">Remove</button> : null}</div><div className="grid gap-4 sm:grid-cols-2"><FormField id={`ingredient-name-${index}`} label="Name" value={ingredient.name} onChange={(event) => updateIngredient(index, 'name', event.target.value)} required /><FormField id={`ingredient-position-${index}`} label="Position" value={index + 1} readOnly /><FormField id={`ingredient-quantity-${index}`} label="Quantity" value={ingredient.quantity} onChange={(event) => updateIngredient(index, 'quantity', event.target.value)} /><FormField id={`ingredient-unit-${index}`} label="Unit" value={ingredient.unit} onChange={(event) => updateIngredient(index, 'unit', event.target.value)} /><FormField id={`ingredient-notes-${index}`} label="Notes" value={ingredient.notes} onChange={(event) => updateIngredient(index, 'notes', event.target.value)} className="sm:col-span-2" /></div></div>)}</div>
      </section>

      <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-2xl font-bold text-stone-950">Steps</h2><p className="mt-1 text-sm text-stone-600">Steps are numbered automatically in their displayed order.</p></div><button type="button" onClick={() => setValues((current) => ({ ...current, steps: [...current.steps, emptyStep()] }))} className="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-100">+ Add step</button></div>
        <div className="mt-6 space-y-5">{values.steps.map((step, index) => <div key={index} className="rounded-2xl border border-stone-200 p-4"><div className="mb-4 flex items-center justify-between"><span className="font-semibold text-stone-800">Step {index + 1}</span>{values.steps.length > 1 ? <button type="button" onClick={() => setValues((current) => ({ ...current, steps: current.steps.filter((_, itemIndex) => itemIndex !== index) }))} className="text-sm font-semibold text-rose-700 hover:text-rose-900">Remove</button> : null}</div><div className="grid gap-4"><FormField id={`step-number-${index}`} label="Step number" value={index + 1} readOnly /><label htmlFor={`step-instruction-${index}`}><span className="text-sm font-semibold text-stone-800">Instruction</span><textarea id={`step-instruction-${index}`} value={step.instruction} onChange={(event) => updateStep(index, event.target.value)} rows="3" required className={textAreaClass(false)} /></label></div></div>)}</div>
      </section>
      <button type="submit" disabled={isSubmitting} className="rounded-full bg-emerald-600 px-6 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? 'Saving...' : submitLabel}</button>
    </form>
  )
}
