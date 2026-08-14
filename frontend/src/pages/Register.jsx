import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { ErrorBanner, Spinner } from '../components/ui/Feedback'

const FIELDS = [
  { name: 'username', label: 'Username', type: 'text', autoComplete: 'username' },
  { name: 'email', label: 'Email address', type: 'email', autoComplete: 'email' },
  { name: 'first_name', label: 'First name (optional)', type: 'text', autoComplete: 'given-name' },
  { name: 'last_name', label: 'Last name (optional)', type: 'text', autoComplete: 'family-name' },
  { name: 'phone_number', label: 'Phone number (optional)', type: 'tel', autoComplete: 'tel' },
  { name: 'password', label: 'Password', type: 'password', autoComplete: 'new-password' },
  { name: 'password_confirm', label: 'Confirm password', type: 'password', autoComplete: 'new-password' },
]

const initialState = Object.fromEntries(FIELDS.map((f) => [f.name, '']))

export default function Register() {
  const { register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [values, setValues] = useState(initialState)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setValues((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setFieldErrors({})
    setSubmitting(true)
    try {
      await register(values)
      toast.success('Account created. Welcome to CineBook!')
      navigate('/', { replace: true })
    } catch (err) {
      const { message, fieldErrors: fe } = extractError(err)
      setError(message)
      setFieldErrors(fe)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="form-card wide card">
      <h2>Create your account</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
        Join CineBook to book seats, track bookings and get recommendations.
      </p>

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit} noValidate>
        <div className="row">
          {FIELDS.map((field) => (
            <div key={field.name} className="field" style={{ flex: '1 1 45%', minWidth: '220px' }}>
              <label className="field-label" htmlFor={field.name}>{field.label}</label>
              <input
                id={field.name}
                name={field.name}
                type={field.type}
                className={`input ${fieldErrors[field.name] ? 'invalid' : ''}`}
                value={values[field.name]}
                onChange={handleChange}
                autoComplete={field.autoComplete}
                required={!field.name.includes('optional') && !['first_name', 'last_name', 'phone_number'].includes(field.name)}
              />
              {fieldErrors[field.name] && (
                <span className="field-error">{fieldErrors[field.name]}</span>
              )}
            </div>
          ))}
        </div>

        <button type="submit" className="btn btn-primary btn-block btn-lg mt-2" disabled={submitting}>
          {submitting ? <Spinner /> : 'Create account'}
        </button>
      </form>

      <div className="divider" />

      <p className="center" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
