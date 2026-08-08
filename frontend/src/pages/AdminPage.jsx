import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { useAuth } from '../auth/useAuth.js'
import { AdminUserModal } from '../components/AdminUserModal.jsx'
import { Button } from '../components/Button.jsx'
import { DataTable } from '../components/DataTable.jsx'
import { ErrorMessage } from '../components/ErrorMessage.jsx'
import { LoadingSpinner } from '../components/LoadingSpinner.jsx'
import { StatusBadge } from '../components/StatusBadge.jsx'
import { api, authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

const roleStyles = {
  USER: 'bg-stone-100 text-stone-700',
  MODERATOR: 'bg-sky-100 text-sky-800',
  ADMIN: 'bg-violet-100 text-violet-800',
}

function RoleBadge({ role }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${roleStyles[role]}`}>{role}</span>
}

function ActiveBadge({ isActive }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${isActive ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>{isActive ? 'Active' : 'Inactive'}</span>
}

function authorName(author) {
  return author?.username || [author?.first_name, author?.last_name].filter(Boolean).join(' ') || 'Recipe Share member'
}

function fullName(user) {
  return [user.first_name, user.last_name].filter(Boolean).join(' ') || 'Not provided'
}

function formatDate(value) {
  if (!value) return 'Unavailable'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

export function AdminPage() {
  const { currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [approvedRecipes, setApprovedRecipes] = useState([])
  const [pendingRecipes, setPendingRecipes] = useState([])
  const [isUsersLoading, setIsUsersLoading] = useState(true)
  const [isRecipesLoading, setIsRecipesLoading] = useState(true)
  const [usersError, setUsersError] = useState('')
  const [recipesError, setRecipesError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [userDialog, setUserDialog] = useState(null)
  const [deactivatingUserId, setDeactivatingUserId] = useState(null)

  const loadUsers = useCallback(async () => {
    setIsUsersLoading(true)
    setUsersError('')
    try {
      setUsers(await authenticatedApi.get('/admin/users'))
    } catch (requestError) {
      setUsersError(getRequestErrorMessage(requestError))
    } finally {
      setIsUsersLoading(false)
    }
  }, [])

  const loadRecipes = useCallback(async () => {
    setIsRecipesLoading(true)
    setRecipesError('')
    try {
      const [approved, pending] = await Promise.all([
        api.get('/recipes'),
        authenticatedApi.get('/recipes/pending'),
      ])
      setApprovedRecipes(approved)
      setPendingRecipes(pending)
    } catch (requestError) {
      setRecipesError(getRequestErrorMessage(requestError))
    } finally {
      setIsRecipesLoading(false)
    }
  }, [])

  useEffect(() => { loadUsers() }, [loadUsers])
  useEffect(() => { loadRecipes() }, [loadRecipes])

  const closeUserDialog = useCallback(() => setUserDialog(null), [])
  const userSaved = async (savedUser, wasCreated) => {
    if (wasCreated) await loadUsers()
    else setUsers((current) => current.map((user) => user.id === savedUser.id ? savedUser : user))
    setFeedback(wasCreated ? `User “${savedUser.username}” was created.` : `User “${savedUser.username}” was updated.`)
    setUserDialog(null)
  }

  const deactivateUser = async (user) => {
    if (!window.confirm('Deactivate this user? Their existing recipes, comments and donation history will remain stored.')) return
    setDeactivatingUserId(user.id)
    setUsersError('')
    setFeedback('')
    try {
      await authenticatedApi.delete(`/admin/users/${user.id}`)
      setUsers((current) => current.map((existing) => existing.id === user.id ? { ...existing, is_active: false } : existing))
      setFeedback(`User “${user.username}” was deactivated.`)
    } catch (requestError) {
      setUsersError(getRequestErrorMessage(requestError))
    } finally {
      setDeactivatingUserId(null)
    }
  }

  const recipes = useMemo(() => [...pendingRecipes, ...approvedRecipes], [approvedRecipes, pendingRecipes])
  const userColumns = [
    { key: 'username', label: 'Username', className: 'font-semibold text-stone-950' },
    { key: 'email', label: 'Email' },
    { key: 'name', label: 'Full name', render: fullName },
    { key: 'role', label: 'Role', render: (user) => <RoleBadge role={user.role} /> },
    { key: 'active', label: 'Status', render: (user) => <ActiveBadge isActive={user.is_active} /> },
    { key: 'created', label: 'Created', className: 'whitespace-nowrap', render: (user) => formatDate(user.created_at) },
    { key: 'actions', label: 'Actions', render: (user) => <div className="flex flex-wrap gap-3"><button type="button" onClick={() => setUserDialog({ user })} className="font-semibold text-emerald-700 hover:text-emerald-900">Edit</button>{user.is_active && user.id !== currentUser.id ? <button type="button" onClick={() => deactivateUser(user)} disabled={deactivatingUserId === user.id} className="font-semibold text-rose-700 hover:text-rose-900 disabled:opacity-50">{deactivatingUserId === user.id ? 'Deactivating...' : 'Deactivate'}</button> : null}</div> },
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
      <p className="mt-2 text-stone-600">Manage accounts and inspect currently available recipe data.</p>
      {feedback ? <p role="status" className="mt-6 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800">{feedback}</p> : null}

      <section className="mt-10 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><h2 className="text-2xl font-bold text-stone-950">Users</h2><p className="mt-1 text-sm text-stone-600">Create, update, deactivate, and reactivate application accounts.</p></div><Button type="button" onClick={() => { setFeedback(''); setUserDialog({ user: null }) }}>Create user</Button></div>
        {usersError ? <div className="mt-5"><ErrorMessage message={usersError} onRetry={loadUsers} /></div> : null}
        {isUsersLoading ? <LoadingSpinner label="Loading users..." /> : null}
        {!isUsersLoading ? <div className="mt-5"><DataTable columns={userColumns} rows={users} getRowKey={(user) => user.id} emptyMessage="No users are available." /></div> : null}
      </section>

      <section className="mt-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><h2 className="text-2xl font-bold text-stone-950">Recipes</h2><p className="mt-1 text-sm text-stone-600">Approved public recipes and pending moderation submissions.</p></div>{!isRecipesLoading && !recipesError ? <div className="flex gap-2"><span className="rounded-full bg-emerald-100 px-3 py-1.5 text-sm font-semibold text-emerald-800">{approvedRecipes.length} approved</span><span className="rounded-full bg-amber-100 px-3 py-1.5 text-sm font-semibold text-amber-800">{pendingRecipes.length} pending</span></div> : null}</div>
        <p className="my-5 text-sm text-stone-600">Draft and rejected recipes are not included because no existing administrative listing endpoint exposes them.</p>
        {recipesError ? <ErrorMessage message={recipesError} onRetry={loadRecipes} /> : null}
        {isRecipesLoading ? <LoadingSpinner label="Loading recipe data..." /> : null}
        {!isRecipesLoading && !recipesError ? <DataTable columns={recipeColumns} rows={recipes} getRowKey={(recipe) => `${recipe.status}-${recipe.id}`} emptyMessage="No approved or pending recipes are currently available." /> : null}
      </section>

      {userDialog ? <AdminUserModal key={userDialog.user?.id || 'create'} user={userDialog.user} currentUserId={currentUser.id} onClose={closeUserDialog} onSaved={userSaved} /> : null}
    </section>
  )
}
