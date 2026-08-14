import { useCallback, useEffect, useState } from 'react'
import { adminUsers } from '../../api/admin'
import { extractError } from '../../api/client'
import { ErrorBanner, LoadingScreen } from '../../components/ui/Feedback'

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    adminUsers
      .list()
      .then(setUsers)
      .catch((err) => setError(extractError(err).message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  if (loading && users.length === 0) return <LoadingScreen label="Loading users..." />

  return (
    <div>
      <div className="section-head">
        <h2 className="section-title">Users</h2>
      </div>

      <ErrorBanner message={error} />

      <div className="card admin-panel table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Joined</th>
              <th>Bookings</th>
              <th>Spent</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && (
              <tr><td colSpan="7" style={{ color: 'var(--text-muted)' }}>No users.</td></tr>
            )}
            {users.map((u) => (
              <tr key={u.id}>
                <td><strong>{u.username}</strong>{!u.is_active && <span className="badge badge-ended"> inactive</span>}</td>
                <td>{u.email || '—'}</td>
                <td>{u.phone_number || '—'}</td>
                <td>{u.date_joined?.slice(0, 10)}</td>
                <td>{u.booking_count}</td>
                <td>₹{Number(u.spent).toLocaleString()}</td>
                <td>{u.is_staff ? <span className="badge badge-confirmed">staff</span> : 'customer'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
