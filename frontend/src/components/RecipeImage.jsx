export function RecipeImage({ recipe, className = '' }) {
  const imageUrl = recipe.image_url || null

  if (imageUrl) {
    return <img src={imageUrl} alt={`A dish from ${recipe.title}`} className={`object-cover ${className}`} />
  }

  return (
    <div aria-label={`Image placeholder for ${recipe.title}`} className={`grid place-items-center bg-linear-to-br from-emerald-700 via-emerald-600 to-teal-500 ${className}`}>
      <span className="text-5xl font-black text-white/90">{recipe.title?.slice(0, 1).toUpperCase() || 'R'}</span>
    </div>
  )
}
