import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { ErrorBanner, Spinner, SuccessBanner } from '../components/ui/Feedback'

export default function ResetPassword() {
  const { confirmPasswordReset } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const uid = searchParams.get('uid') || ''
  const token = searchParams.get('token') || ''

  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!uid || !token) {
    return (
      <div className="form-card card">
        <h2>Invalid reset link</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          This reset link is incomplete or has expired. Request a new one.
        </p>
        <Link to="/forgot-password" className="btn btn-primary btn-block mt-2">
          Request a new link
        </Link>
      </div>
    )
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)
    try {
      await confirmPasswordReset({ uidb64: uid, token, new_password: newPassword, new_password_confirm: confirm })
      setSuccess('Password reset successfully. You can now log in.')
      toast.success('Password updated!')
      setTimeout(() => navigate('/login', { replace: true }), 1500)
    } catch (err) {
      const { message, fieldErrors } = extractError(err)
      setError(fieldErrors.new_password_confirm || fieldErrors.new_password || message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="form-card card">
      <h2>Set a new password</h2>

      <ErrorBanner message={error} />
      <SuccessBanner message={success} />

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label className="field-label" htmlFor="newPassword">New password</label>
          <input
            id="newPassword"
            type="password"
            className="input"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
            autoFocus
            required
          />
        </div>

        <div className="field">
          <label className="field-label" htmlFor="confirm">Confirm new password</label>
          <input
            id="confirm"
            type="password"
            className="input"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary btn-block btn-lg mt-2" disabled={submitting}>
          {submitting ? <Spinner /> : 'Reset password'}
        </button>
      </form>

      <div className="divider" />

      <p className="center" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        <Link to="/login">Back to login</Link>
      </p>
    </div>
  )
}
