import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../auth/useAuth.js'
import { AuthCard } from '../components/AuthCard.jsx'
import { FormField } from '../components/FormField.jsx'
import { getRequestErrorMessage } from '../lib/formErrors.js'

const initialValues = {
  email: '',
  username: '',
  password: '',
  first_name: '',
  last_name: '',
}

function validate(values) {
  const errors = {}
  if (!values.email.trim()) errors.email = 'Email is required.'
  else if (!/^\S+@\S+\.\S+$/.test(values.email)) errors.email = 'Enter a valid email address.'
  if (!values.username.trim()) errors.username = 'Username is required.'
  else if (values.username.trim().length < 3) errors.username = 'Username must be at least 3 characters.'
  if (!values.first_name.trim()) errors.first_name = 'First name is required.'
  if (!values.last_name.trim()) errors.last_name = 'Last name is required.'
  if (!values.password) errors.password = 'Password is required.'
  else if (values.password.length < 8) errors.password = 'Password must be at least 8 characters.'
  return errors
}

export function RegisterPage() {
  const { register } = useAuth()
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
      await register({
        email: values.email.trim(),
        username: values.username.trim(),
        password: values.password,
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
      })
      navigate('/login', {
        replace: true,
        state: { registrationSuccess: 'Account created. You can log in now.' },
      })
    } catch (error) {
      setRequestError(getRequestErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthCard eyebrow="Join the table" title="Create your account">
      {requestError ? <p role="alert" className="mb-5 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">{requestError}</p> : null}
      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <div className="grid gap-5 sm:grid-cols-2">
          <FormField id="register-first-name" label="First name" name="first_name" autoComplete="given-name" value={values.first_name} onChange={updateValue} error={errors.first_name} />
          <FormField id="register-last-name" label="Last name" name="last_name" autoComplete="family-name" value={values.last_name} onChange={updateValue} error={errors.last_name} />
        </div>
        <FormField id="register-email" label="Email" name="email" type="email" autoComplete="email" value={values.email} onChange={updateValue} error={errors.email} />
        <FormField id="register-username" label="Username" name="username" autoComplete="username" value={values.username} onChange={updateValue} error={errors.username} />
        <FormField id="register-password" label="Password" name="password" type="password" autoComplete="new-password" value={values.password} onChange={updateValue} error={errors.password} />
        <button type="submit" disabled={isSubmitting} className="w-full rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? 'Creating account…' : 'Create account'}</button>
      </form>
      <p className="mt-6 text-sm text-stone-600">Already registered? <Link to="/login" className="font-semibold text-emerald-700 hover:text-emerald-800">Log in</Link>.</p>
    </AuthCard>
  )
}
