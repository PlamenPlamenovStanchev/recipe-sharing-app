import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { authenticatedApi, api } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'
import { EmptyState } from './EmptyState.jsx'
import { LoadingSpinner } from './LoadingSpinner.jsx'

function authorName(author) {
  return author?.username || [author?.first_name, author?.last_name].filter(Boolean).join(' ') || 'Recipe Share member'
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

function canManageComment(comment, user) {
  return comment.author?.id === user?.id || ['MODERATOR', 'ADMIN'].includes(user?.role)
}

export function CommentsSection({ recipeId, currentUser, isAuthenticated }) {
  const [comments, setComments] = useState([])
  const [content, setContent] = useState('')
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  const loadComments = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      setComments(await api.get(`/recipes/${recipeId}/comments`))
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsLoading(false)
    }
  }, [recipeId])

  useEffect(() => { loadComments() }, [loadComments])

  const createComment = async (event) => {
    event.preventDefault()
    const normalizedContent = content.trim()
    if (normalizedContent.length < 2 || normalizedContent.length > 1000) {
      setError('A comment must contain between 2 and 1000 characters.')
      return
    }
    setIsSaving(true)
    setError('')
    try {
      const comment = await authenticatedApi.post(`/recipes/${recipeId}/comments`, { content: normalizedContent })
      setComments((current) => [...current, comment])
      setContent('')
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSaving(false)
    }
  }

  const updateComment = async (commentId) => {
    const normalizedContent = editing.content.trim()
    if (normalizedContent.length < 2 || normalizedContent.length > 1000) {
      setError('A comment must contain between 2 and 1000 characters.')
      return
    }
    setIsSaving(true)
    setError('')
    try {
      const updated = await authenticatedApi.put(`/comments/${commentId}`, { content: normalizedContent })
      setComments((current) => current.map((comment) => comment.id === commentId ? updated : comment))
      setEditing(null)
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSaving(false)
    }
  }

  const deleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment? This cannot be undone.')) return
    setIsSaving(true)
    setError('')
    try {
      await authenticatedApi.delete(`/comments/${commentId}`)
      setComments((current) => current.filter((comment) => comment.id !== commentId))
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="mt-12 border-t border-stone-200 pt-10">
      <h2 className="text-3xl font-black tracking-tight text-stone-950">Comments</h2>
      {error ? <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}
      {isAuthenticated ? <form onSubmit={createComment} className="mt-6 rounded-3xl border border-stone-200 bg-white p-5 shadow-sm"><label htmlFor="new-comment" className="text-sm font-semibold text-stone-800">Join the conversation</label><textarea id="new-comment" value={content} onChange={(event) => setContent(event.target.value)} maxLength="1000" rows="3" placeholder="Share a helpful thought..." className="mt-2 block w-full rounded-xl border border-stone-300 px-4 py-3 outline-none focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100" /><div className="mt-3 flex items-center justify-between gap-3"><span className="text-xs text-stone-500">{content.trim().length}/1000 characters</span><button type="submit" disabled={isSaving} className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">Post comment</button></div></form> : <p className="mt-5 rounded-2xl bg-stone-100 px-4 py-3 text-sm text-stone-700"><Link to="/login" className="font-semibold text-emerald-700">Log in</Link> to leave a comment.</p>}
      {isLoading ? <LoadingSpinner label="Loading comments..." /> : null}
      {!isLoading && !error && comments.length === 0 ? <div className="mt-6"><EmptyState title="No comments yet" message="Be the first to start the conversation." /></div> : null}
      {!isLoading && comments.length > 0 ? <div className="mt-6 space-y-4">{comments.map((comment) => <article key={comment.id} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-semibold text-stone-950">{authorName(comment.author)}</p><p className="mt-1 text-xs text-stone-500">{formatDate(comment.updated_at || comment.created_at)}</p></div>{canManageComment(comment, currentUser) ? <div className="flex gap-3 text-sm font-semibold"><button type="button" onClick={() => setEditing({ id: comment.id, content: comment.content })} className="text-emerald-700 hover:text-emerald-900">Edit</button><button type="button" onClick={() => deleteComment(comment.id)} disabled={isSaving} className="text-rose-700 hover:text-rose-900">Delete</button></div> : null}</div>{editing?.id === comment.id ? <div className="mt-4"><textarea value={editing.content} onChange={(event) => setEditing((current) => ({ ...current, content: event.target.value }))} maxLength="1000" rows="3" className="block w-full rounded-xl border border-stone-300 px-4 py-3 outline-none focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100" /><div className="mt-3 flex gap-3"><button type="button" onClick={() => updateComment(comment.id)} disabled={isSaving} className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">Save</button><button type="button" onClick={() => setEditing(null)} className="text-sm font-semibold text-stone-700">Cancel</button></div></div> : <p className="mt-4 whitespace-pre-wrap leading-7 text-stone-700">{comment.content}</p>}</article>)}</div> : null}
    </section>
  )
}
