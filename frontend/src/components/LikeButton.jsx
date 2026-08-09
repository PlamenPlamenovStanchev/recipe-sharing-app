import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { authenticatedApi, api } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

export function LikeButton({ recipeId, initialCount = 0, initiallyLiked = false, isAuthenticated, onCountChange }) {
  const [count, setCount] = useState(initialCount)
  const [isLiked, setIsLiked] = useState(initiallyLiked)
  const [error, setError] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  const requestInFlight = useRef(false)

  useEffect(() => {
    let active = true
    api.get(`/recipes/${recipeId}/likes`)
      .then(({ count: serverCount }) => {
        if (!active || requestInFlight.current) return
        setCount(serverCount)
        onCountChange?.(serverCount)
      })
      .catch(() => {})
    return () => { active = false }
  }, [onCountChange, recipeId])

  const toggleLike = async () => {
    if (requestInFlight.current) return
    requestInFlight.current = true
    setIsUpdating(true)
    setError('')
    const wasLiked = isLiked
    const nextCount = Math.max(0, count + (wasLiked ? -1 : 1))
    setIsLiked(!wasLiked)
    setCount(nextCount)
    onCountChange?.(nextCount)
    try {
      if (wasLiked) await authenticatedApi.delete(`/recipes/${recipeId}/likes`)
      else await authenticatedApi.post(`/recipes/${recipeId}/likes`)
    } catch (requestError) {
      setIsLiked(wasLiked)
      setCount(count)
      onCountChange?.(count)
      setError(getRequestErrorMessage(requestError))
    } finally {
      requestInFlight.current = false
      setIsUpdating(false)
    }
  }

  if (!isAuthenticated) {
    return <div><Link to="/login" className="rounded-full bg-rose-50 px-3 py-1.5 text-sm font-semibold text-rose-700 hover:bg-rose-100">{count} likes · Log in to like</Link></div>
  }

  return (
    <div>
      <button type="button" onClick={toggleLike} disabled={isUpdating} aria-pressed={isLiked} className={`rounded-full px-3 py-1.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${isLiked ? 'bg-rose-600 text-white hover:bg-rose-700' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'}`}>{isUpdating ? 'Updating...' : `${isLiked ? '♥ Liked' : '♡ Like'} · ${count}`}</button>
      {error ? <p role="alert" className="mt-2 text-sm text-rose-700">{error}</p> : null}
    </div>
  )
}
