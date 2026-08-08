import { useEffect, useState } from 'react'
import { authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'

const MAX_IMAGE_SIZE = 5 * 1024 * 1024
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function RecipeImageUpload({ recipe, onUploaded }) {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(recipe.image_url || null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    if (!file) setPreviewUrl(recipe.image_url || null)
  }, [file, recipe.image_url])

  useEffect(() => () => {
    if (previewUrl?.startsWith('blob:')) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  const chooseFile = (event) => {
    const selectedFile = event.target.files?.[0] || null
    setError('')
    setSuccess('')
    if (!selectedFile) return
    if (!ACCEPTED_TYPES.includes(selectedFile.type)) {
      setError('Choose a JPEG, PNG, or WebP image.')
      return
    }
    if (selectedFile.size === 0 || selectedFile.size > MAX_IMAGE_SIZE) {
      setError('Choose a non-empty image smaller than 5 MB.')
      return
    }
    if (previewUrl?.startsWith('blob:')) URL.revokeObjectURL(previewUrl)
    setFile(selectedFile)
    setPreviewUrl(URL.createObjectURL(selectedFile))
  }

  const upload = async () => {
    if (!file) {
      setError('Choose an image before uploading.')
      return
    }
    setIsUploading(true)
    setError('')
    setSuccess('')
    try {
      const data = new FormData()
      data.append('image', file)
      const uploaded = await authenticatedApi.post(`/recipes/${recipe.id}/image`, data)
      setFile(null)
      setPreviewUrl(uploaded.image_url || null)
      setSuccess('Image uploaded.')
      onUploaded(uploaded)
    } catch (requestError) {
      setError(getRequestErrorMessage(requestError))
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
      <h2 className="text-2xl font-bold text-stone-950">Recipe image</h2>
      <p className="mt-1 text-sm text-stone-600">JPEG, PNG, or WebP. Maximum file size: 5 MB.</p>
      {previewUrl ? <img src={previewUrl} alt="Recipe upload preview" className="mt-5 aspect-4/3 w-full max-w-md rounded-2xl object-cover" /> : null}
      <label className="mt-5 block" htmlFor="recipe-image"><span className="text-sm font-semibold text-stone-800">Choose image</span><input id="recipe-image" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} className="mt-2 block w-full text-sm text-stone-700 file:mr-4 file:rounded-full file:border-0 file:bg-emerald-50 file:px-4 file:py-2 file:font-semibold file:text-emerald-800 hover:file:bg-emerald-100" /></label>
      {error ? <p role="alert" className="mt-3 text-sm text-rose-700">{error}</p> : null}
      {success ? <p role="status" className="mt-3 text-sm text-emerald-700">{success}</p> : null}
      <button type="button" onClick={upload} disabled={!file || isUploading} className="mt-5 rounded-full bg-stone-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60">{isUploading ? 'Uploading...' : 'Upload image'}</button>
    </section>
  )
}
