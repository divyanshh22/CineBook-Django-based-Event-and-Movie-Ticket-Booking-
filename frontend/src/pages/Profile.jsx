import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { Badge, ErrorBanner, Spinner } from '../components/ui/Feedback'

export default function Profile() {
  const { user, updateProfile, changePassword } = useAuth()
  const toast = useToast()

  const [profileForm, setProfileForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone_number: user?.phone_number || '',
  })
  const [profileError, setProfileError] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)

  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  })
  const [passwordError, setPasswordError] = useState('')
  const [passwordFieldErrors, setPasswordFieldErrors] = useState({})
  const [savingPassword, setSavingPassword] = useState(false)

  const handleProfileSubmit = async (event) => {
    event.preventDefault()
    setProfileError('')
    setSavingProfile(true)
    try {
      await updateProfile(profileForm)
      toast.success('Profile updated.')
    } catch (err) {
      const { message } = extractError(err)
      setProfileError(message)
    } finally {
      setSavingProfile(false)
    }
  }

  const handlePasswordSubmit = async (event) => {
    event.preventDefault()
    setPasswordError('')
    setPasswordFieldErrors({})
    setSavingPassword(true)
    try {
      await changePassword(passwordForm)
      setPasswordForm({ old_password: '', new_password: '', new_password_confirm: '' })
      toast.success('Password changed. Please log in again.')
    } catch (err) {
      const { message, fieldErrors } = extractError(err)
      setPasswordError(message)
      setPasswordFieldErrors(fieldErrors)
    } finally {
      setSavingPassword(false)
    }
  }

  return (
    <div className="container">
      <h2>My profile</h2>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="row" style={{ alignItems: 'center' }}>
          <span className="avatar-lg">
            {(user?.full_name || user?.username || '?').slice(0, 1).toUpperCase()}
          </span>
          <div>
            <h3 style={{ marginBottom: '0.25rem' }}>{user?.full_name || user?.username}</h3>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{user?.email}</div>
            <div className="row mt-1" style={{ gap: '0.4rem' }}>
              <Badge variant={user?.is_email_verified ? 'success' : 'warning'}>
                {user?.is_email_verified ? 'Email verified' : 'Email not verified'}
              </Badge>
              {user?.is_staff && <Badge variant="accent">Staff</Badge>}
            </div>
          </div>
        </div>
      </div>

      <div className="row" style={{ alignItems: 'flex-start' }}>
        {/* Profile details */}
        <div className="card" style={{ flex: '1 1 320px', padding: '1.5rem' }}>
          <h3>Account details</h3>
          <ErrorBanner message={profileError} />
          <form onSubmit={handleProfileSubmit}>
            <div className="field">
              <label className="field-label" htmlFor="first_name">First name</label>
              <input
                id="first_name"
                className="input"
                value={profileForm.first_name}
                onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="last_name">Last name</label>
              <input
                id="last_name"
                className="input"
                value={profileForm.last_name}
                onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="phone_number">Phone number</label>
              <input
                id="phone_number"
                className="input"
                value={profileForm.phone_number}
                onChange={(e) => setProfileForm({ ...profileForm, phone_number: e.target.value })}
                placeholder="+91 ..."
              />
            </div>
            <button type="submit" className="btn btn-primary mt-2" disabled={savingProfile}>
              {savingProfile ? <Spinner /> : 'Save changes'}
            </button>
          </form>
        </div>

        {/* Change password */}
        <div className="card" style={{ flex: '1 1 320px', padding: '1.5rem' }}>
          <h3>Change password</h3>
          <ErrorBanner message={passwordError} />
          <form onSubmit={handlePasswordSubmit}>
            <div className="field">
              <label className="field-label" htmlFor="old_password">Current password</label>
              <input
                id="old_password"
                type="password"
                className="input"
                value={passwordForm.old_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                autoComplete="current-password"
                required
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="new_password">New password</label>
              <input
                id="new_password"
                type="password"
                className={`input ${passwordFieldErrors.new_password ? 'invalid' : ''}`}
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                autoComplete="new-password"
                required
              />
              {passwordFieldErrors.new_password && (
                <span className="field-error">{passwordFieldErrors.new_password}</span>
              )}
            </div>
            <div className="field">
              <label className="field-label" htmlFor="new_password_confirm">Confirm new password</label>
              <input
                id="new_password_confirm"
                type="password"
                className={`input ${passwordFieldErrors.new_password_confirm ? 'invalid' : ''}`}
                value={passwordForm.new_password_confirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password_confirm: e.target.value })}
                autoComplete="new-password"
                required
              />
              {passwordFieldErrors.new_password_confirm && (
                <span className="field-error">{passwordFieldErrors.new_password_confirm}</span>
              )}
            </div>
            <button type="submit" className="btn btn-secondary mt-2" disabled={savingPassword}>
              {savingPassword ? <Spinner /> : 'Update password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
