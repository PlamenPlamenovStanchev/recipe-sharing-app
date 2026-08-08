import { Link } from 'react-router'
import { RecipeImage } from './RecipeImage.jsx'

function formatDate(value) {
  if (!value) return 'Recently added'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

function authorName(author) {
  return author?.username || [author?.first_name, author?.last_name].filter(Boolean).join(' ') || 'Recipe Share member'
}

export function RecipeCard({ recipe }) {
  return (
    <Link to={`/recipes/${recipe.id}`} className="group overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm transition hover:-translate-y-1 hover:border-emerald-200 hover:shadow-lg focus:outline-none focus:ring-4 focus:ring-emerald-100">
      <RecipeImage recipe={recipe} className="aspect-4/3 w-full" />
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-xl font-bold tracking-tight text-stone-950 group-hover:text-emerald-700">{recipe.title}</h2>
          <span className="shrink-0 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700">{recipe.like_count ?? 0} likes</span>
        </div>
        <p className="mt-3 text-sm text-stone-600">By {authorName(recipe.author)}</p>
        <p className="mt-1 text-sm text-stone-500">{formatDate(recipe.created_at)}</p>
      </div>
    </Link>
  )
}
