import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { ErrorBanner, Spinner } from '../components/ui/Feedback'

export default function Login() {
  const { login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setFieldErrors({})
    setSubmitting(true)
    try {
      await login(username.trim(), password)
      toast.success('Welcome back!')
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      const { message, fieldErrors: fe } = extractError(err)
      setError(message)
      setFieldErrors(fe)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="form-card card">
      <h2>Welcome back</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
        Log in to book movies, events and manage your tickets.
      </p>

      <ErrorBanner message={error} />

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label className="field-label" htmlFor="username">Username or email</label>
          <input
            id="username"
            className={`input ${fieldErrors.detail ? 'invalid' : ''}`}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
            required
          />
        </div>

        <div className="field">
          <label className="field-label" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <Link to="/forgot-password" style={{ fontSize: '0.85rem' }}>Forgot password?</Link>
        </div>

        <button type="submit" className="btn btn-primary btn-block btn-lg mt-2" disabled={submitting}>
          {submitting ? <Spinner /> : 'Log in'}
        </button>
      </form>

      <div className="divider" />

      <p className="center" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        New to CineBook? <Link to="/register">Create an account</Link>
      </p>
    </div>
  )
}
