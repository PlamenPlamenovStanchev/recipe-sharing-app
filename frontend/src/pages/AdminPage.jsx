import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { DataTable } from '../components/DataTable.jsx'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { LoadingSpinner } from '../components/LoadingSpinner.jsx'
import { StatusBadge } from '../components/StatusBadge.jsx'
import { api, authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

function authorName(author) {
  return author?.username || [author?.first_name, author?.last_name].filter(Boolean).join(' ') || 'Recipe Share member'
}

function formatDate(value) {
  if (!value) return 'Unavailable'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

export function AdminPage() {
  const [approvedRecipes, setApprovedRecipes] = useState([])
  const [pendingRecipes, setPendingRecipes] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadRecipes = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const [approved, pending] = await Promise.all([
        api.get('/recipes'),
        authenticatedApi.get('/recipes/pending'),
      ])
      setApprovedRecipes(approved)
      setPendingRecipes(pending)
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { loadRecipes() }, [loadRecipes])

  const recipes = useMemo(() => [...pendingRecipes, ...approvedRecipes], [approvedRecipes, pendingRecipes])
  const userColumns = [
    { key: 'username', label: 'User' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role' },
    { key: 'actions', label: 'Actions' },
  ]
  const recipeColumns = [
    { key: 'title', label: 'Recipe', className: 'min-w-56 font-semibold text-stone-950' },
    { key: 'author', label: 'Author', render: (recipe) => authorName(recipe.author) },
    { key: 'status', label: 'Status', render: (recipe) => <StatusBadge status={recipe.status} /> },
    { key: 'date', label: 'Submitted / created', className: 'whitespace-nowrap', render: (recipe) => formatDate(recipe.submitted_at || recipe.created_at) },
    { key: 'likes', label: 'Likes', render: (recipe) => recipe.like_count ?? 0 },
    { key: 'actions', label: 'Actions', render: (recipe) => <Link to={`/recipes/${recipe.id}`} className="font-semibold text-emerald-700 hover:text-emerald-900">Open</Link> },
  ]

  return (
    <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">Administration</p>
      <h1 className="mt-3 text-4xl font-black tracking-tight text-stone-950">Admin dashboard</h1>
      <p className="mt-2 text-stone-600">A central view of currently available administration data.</p>

      <section className="mt-10 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><h2 className="text-2xl font-bold text-stone-950">Users</h2><p className="mt-1 text-sm text-stone-600">User administration foundation.</p></div><button type="button" disabled title="No backend user-management endpoint is available" className="cursor-not-allowed rounded-full bg-stone-200 px-4 py-2 text-sm font-semibold text-stone-500">Add user unavailable</button></div>
        <p className="my-5 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">User listing and CRUD operations are unavailable because the backend does not currently expose admin user-management endpoints.</p>
        <DataTable columns={userColumns} rows={[]} getRowKey={(user) => user.id} emptyMessage="No user data requested: a user-list endpoint is not available." />
      </section>

      <section className="mt-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><h2 className="text-2xl font-bold text-stone-950">Recipes</h2><p className="mt-1 text-sm text-stone-600">Approved public recipes and pending moderation submissions.</p></div>{!isLoading && !error ? <div className="flex gap-2"><span className="rounded-full bg-emerald-100 px-3 py-1.5 text-sm font-semibold text-emerald-800">{approvedRecipes.length} approved</span><span className="rounded-full bg-amber-100 px-3 py-1.5 text-sm font-semibold text-amber-800">{pendingRecipes.length} pending</span></div> : null}</div>
        <p className="my-5 text-sm text-stone-600">Draft and rejected recipes are not included because no existing administrative listing endpoint exposes them.</p>
        {error ? <ErrorMessage message={error} onRetry={loadRecipes} /> : null}
        {isLoading ? <LoadingSpinner label="Loading recipe data..." /> : null}
        {!isLoading && !error ? <DataTable columns={recipeColumns} rows={recipes} getRowKey={(recipe) => `${recipe.status}-${recipe.id}`} emptyMessage="No approved or pending recipes are currently available." /> : null}
      </section>
    </section>
  )
}
