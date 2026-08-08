import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { useAuth } from '../auth/useAuth.js'
import { AuthCard } from '../components/AuthCard.jsx'
import { FormField } from '../components/FormField.jsx'
import { getRequestErrorMessage } from '../lib/formErrors.js'

const initialValues = { email: '', password: '' }

function validate(values) {
  const errors = {}
  if (!values.email.trim()) errors.email = 'Email is required.'
  else if (!/^\S+@\S+\.\S+$/.test(values.email)) errors.email = 'Enter a valid email address.'
  if (!values.password) errors.password = 'Password is required.'
  return errors
}

export function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [requestError, setRequestError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const updateValue = (event) => {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: undefined }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const nextErrors = validate(values)
    setErrors(nextErrors)
    setRequestError('')
    if (Object.keys(nextErrors).length > 0) return

    setIsSubmitting(true)
    try {
      await login({ email: values.email.trim(), password: values.password })
      navigate(location.state?.from || '/recipes', { replace: true })
    } catch (error) {
      setRequestError(getRequestErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthCard eyebrow="Welcome back" title="Log in to Recipe Share">
      {location.state?.registrationSuccess ? <p className="mb-5 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">{location.state.registrationSuccess}</p> : null}
      {requestError ? <p role="alert" className="mb-5 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">{requestError}</p> : null}
      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <FormField id="login-email" label="Email" name="email" type="email" autoComplete="email" value={values.email} onChange={updateValue} error={errors.email} />
        <FormField id="login-password" label="Password" name="password" type="password" autoComplete="current-password" value={values.password} onChange={updateValue} error={errors.password} />
        <button type="submit" disabled={isSubmitting} className="w-full rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? 'Logging in…' : 'Log in'}</button>
      </form>
      <p className="mt-6 text-sm text-stone-600">New here? <Link to="/register" className="font-semibold text-emerald-700 hover:text-emerald-800">Create an account</Link>.</p>
    </AuthCard>
  )
}
