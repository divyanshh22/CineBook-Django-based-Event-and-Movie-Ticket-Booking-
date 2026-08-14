import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { ErrorBanner, Spinner, SuccessBanner } from '../components/ui/Feedback'

export default function ForgotPassword() {
  const { requestPasswordReset } = useAuth()
  const toast = useToast()

  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [devLink, setDevLink] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setDevLink('')
    setSubmitting(true)
    try {
      const data = await requestPasswordReset(email.trim())
      setSuccess('If that email exists, a reset link has been sent.')
      // In development the backend echoes the token so the flow can be tested.
      if (data?.dev_uidb64 && data?.dev_token) {
        setDevLink(`${window.location.origin}/reset-password?uid=${data.dev_uidb64}&token=${data.dev_token}`)
      }
    } catch (err) {
      const { message } = extractError(err)
      setError(message)
    } finally {
      setSubmitting(false)
      toast.info('Check your inbox for the reset link.')
    }
  }

  return (
    <div className="form-card card">
      <h2>Reset your password</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
        Enter your account email and we'll send you a link to set a new password.
      </p>

      <ErrorBanner message={error} />
      <SuccessBanner message={success} />

      {devLink && (
        <div className="form-success" style={{ wordBreak: 'break-all', fontSize: '0.8rem' }}>
          <strong>Dev link:</strong>{' '}
          <a href={devLink} style={{ color: 'inherit' }}>{devLink}</a>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label className="field-label" htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            autoFocus
            required
          />
        </div>

        <button type="submit" className="btn btn-primary btn-block btn-lg mt-2" disabled={submitting}>
          {submitting ? <Spinner /> : 'Send reset link'}
        </button>
      </form>

      <div className="divider" />

      <p className="center" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Remembered it? <Link to="/login">Back to login</Link>
      </p>
    </div>
  )
}
