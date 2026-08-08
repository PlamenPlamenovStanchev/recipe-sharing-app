import { useState } from 'react'
import { authenticatedApi } from '../lib/api.js'
import { getRequestErrorMessage } from '../lib/formErrors.js'
import { Button } from './Button.jsx'
import { FormField } from './FormField.jsx'
import { Modal } from './Modal.jsx'

const roles = ['USER', 'MODERATOR', 'ADMIN']

function initialValues(user) {
  return {
    email: user?.email || '',
    username: user?.username || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    password: '',
    role: user?.role || 'USER',
    is_active: user?.is_active ?? true,
  }
}

function validate(values, isCreating) {
  const errors = {}
  if (!/^\S+@\S+\.\S+$/.test(values.email.trim())) errors.email = 'Enter a valid email address.'
  if (!/^[A-Za-z0-9_]{3,30}$/.test(values.username.trim())) errors.username = 'Use 3-30 letters, numbers, or underscores.'
  if (!values.first_name.trim()) errors.first_name = 'First name is required.'
  if (!values.last_name.trim()) errors.last_name = 'Last name is required.'
  if (isCreating && (values.password.length < 8 || !/[A-Z]/.test(values.password) || !/[a-z]/.test(values.password) || !/\d/.test(values.password))) errors.password = 'Use at least 8 characters with uppercase, lowercase, and a digit.'
  if (!roles.includes(values.role)) errors.role = 'Choose a valid role.'
  return errors
}

export function AdminUserModal({ user, currentUserId, onClose, onSaved }) {
  const isCreating = !user
  const isCurrentUser = user?.id === currentUserId
  const [values, setValues] = useState(() => initialValues(user))
  const [errors, setErrors] = useState({})
  const [requestError, setRequestError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const updateValue = (event) => {
    const { name, value, type, checked } = event.target
    setValues((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
    setErrors((current) => ({ ...current, [name]: undefined }))
  }

  const submit = async (event) => {
    event.preventDefault()
    const nextErrors = validate(values, isCreating)
    setErrors(nextErrors)
    setRequestError('')
    if (Object.keys(nextErrors).length > 0) return

    const payload = {
      email: values.email.trim(),
      username: values.username.trim(),
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
      role: values.role,
      is_active: values.is_active,
    }
    if (isCreating) payload.password = values.password

    setIsSubmitting(true)
    try {
      const savedUser = isCreating
        ? await authenticatedApi.post('/admin/users', payload)
        : await authenticatedApi.put(`/admin/users/${user.id}`, payload)
      await onSaved(savedUser, isCreating)
    } catch (error) {
      setRequestError(getRequestErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal isOpen title={isCreating ? 'Create user' : `Edit ${user.username}`} onClose={onClose}>
      {requestError ? <p role="alert" className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{requestError}</p> : null}
      <form onSubmit={submit} className="space-y-4" noValidate>
        <div className="grid gap-4 sm:grid-cols-2"><FormField id="admin-first-name" label="First name" name="first_name" value={values.first_name} onChange={updateValue} error={errors.first_name} /><FormField id="admin-last-name" label="Last name" name="last_name" value={values.last_name} onChange={updateValue} error={errors.last_name} /></div>
        <FormField id="admin-email" label="Email" name="email" type="email" value={values.email} onChange={updateValue} error={errors.email} />
        <FormField id="admin-username" label="Username" name="username" value={values.username} onChange={updateValue} error={errors.username} />
        {isCreating ? <FormField id="admin-password" label="Password" name="password" type="password" autoComplete="new-password" value={values.password} onChange={updateValue} error={errors.password} /> : null}
        <label className="block" htmlFor="admin-role"><span className="text-sm font-semibold text-stone-800">Role</span><select id="admin-role" name="role" value={values.role} onChange={updateValue} disabled={isCurrentUser} className="mt-2 block w-full rounded-xl border border-stone-300 bg-white px-4 py-3 outline-none focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 disabled:bg-stone-100">{roles.map((role) => <option key={role} value={role}>{role}</option>)}</select>{errors.role ? <span className="mt-1 block text-sm text-rose-700">{errors.role}</span> : null}</label>
        <label className="flex items-start gap-3 rounded-xl border border-stone-200 p-4"><input type="checkbox" name="is_active" checked={values.is_active} onChange={updateValue} disabled={isCurrentUser} className="mt-0.5 size-4 accent-emerald-600" /><span><strong className="block text-sm text-stone-900">Active account</strong><span className="text-xs text-stone-600">Inactive users cannot authenticate. Reactivation preserves their existing content and history.</span></span></label>
        {isCurrentUser ? <p className="text-xs text-amber-800">Your own ADMIN role and active status are protected. The backend enforces this rule.</p> : null}
        <div className="flex justify-end gap-3 pt-2"><Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>Cancel</Button><Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : isCreating ? 'Create user' : 'Save changes'}</Button></div>
      </form>
    </Modal>
  )
}
