import { useCallback, useEffect, useState } from 'react'
import { adminBookings } from '../../api/admin'
import { extractError } from '../../api/client'
import { ErrorBanner, LoadingScreen } from '../../components/ui/Feedback'

const STATUS_BADGE = { confirmed: 'confirmed', pending: 'pending', cancelled: 'cancelled', failed: 'failed' }

export default function Bookings() {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    adminBookings
      .list()
      .then(setBookings)
      .catch((err) => setError(extractError(err).message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  const visible = filter === 'all' ? bookings : bookings.filter((b) => b.status === filter)

  if (loading && bookings.length === 0) return <LoadingScreen label="Loading bookings..." />

  return (
    <div>
      <div className="section-head">
        <h2 className="section-title">Bookings</h2>
        <div className="filter-tabs">
          {['all', 'confirmed', 'pending', 'cancelled', 'failed'].map((f) => (
            <button
              key={f}
              className={`chip ${filter === f ? 'chip-on' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <ErrorBanner message={error} />

      <div className="card admin-panel table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>User</th>
              <th>Movie</th>
              <th>Show</th>
              <th>Seats</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 && (
              <tr><td colSpan="7" style={{ color: 'var(--text-muted)' }}>No bookings.</td></tr>
            )}
            {visible.map((b) => (
              <tr key={b.id}>
                <td><strong>{b.booking_code}</strong></td>
                <td>{b.username}</td>
                <td>{b.movie}</td>
                <td>
                  {b.show_date} · {b.start_time}
                </td>
                <td>{b.seats.join(', ')}</td>
                <td>₹{b.total.toFixed(2)}</td>
                <td><span className={`badge badge-${STATUS_BADGE[b.status] || b.status}`}>{b.status_display || b.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
