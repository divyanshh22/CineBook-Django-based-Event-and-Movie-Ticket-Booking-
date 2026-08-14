import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchMyBookings, ticketUrl } from '../api/booking'
import { extractError } from '../api/client'
import { Badge, EmptyState, ErrorBanner, LoadingScreen } from '../components/ui/Feedback'

const TABS = [
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'past', label: 'Past' },
]

function statusVariant(status) {
  if (status === 'confirmed') return 'success'
  if (status === 'cancelled') return 'danger'
  return 'warning'
}

function BookingCard({ booking }) {
  const dateLabel = new Date(`${booking.show_date}T00:00:00`).toLocaleDateString(undefined, {
    weekday: 'short', day: 'numeric', month: 'short',
  })
  return (
    <div className="card booking-card">
      {booking.movie_poster && (
        <div className="booking-poster">
          <img src={booking.movie_poster} alt={`${booking.movie} poster`} loading="lazy" />
        </div>
      )}
      <div className="booking-info">
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0 }}>{booking.movie}</h3>
          <Badge variant={statusVariant(booking.status)}>{booking.status_display}</Badge>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
          🎦 {booking.cinema}, {booking.cinema_city} · Screen {booking.screen} ({booking.screen_type})
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
          📅 {dateLabel} at {booking.start_time}
        </div>
        <div className="movie-genres mt-1">
          {booking.seats.map((s) => (
            <span key={s.seat}>{s.seat}</span>
          ))}
        </div>
      </div>
      <div className="booking-actions">
        <div className="rating-big">₹{Number(booking.total).toFixed(2)}</div>
        <div style={{ color: 'var(--text-faint)', fontSize: '0.8rem' }}>{booking.booking_code}</div>
        <Link to={`/bookings/${booking.booking_code}`} className="btn btn-ghost btn-sm">
          View &amp; ticket
        </Link>
        {booking.status === 'confirmed' && (
          <a className="btn btn-secondary btn-sm" href={ticketUrl(booking.booking_code)}>
            ⬇️ Download
          </a>
        )}
      </div>
    </div>
  )
}

export default function MyBookings() {
  const [tab, setTab] = useState('upcoming')
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await fetchMyBookings(tab)
      setBookings(data.results || data)
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [tab])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="container">
      <div className="section-head">
        <h2 className="section-title">My bookings</h2>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingScreen label="Loading bookings..." />
      ) : bookings.length === 0 ? (
        <EmptyState
          icon="🎟️"
          title={`No ${tab} bookings`}
          description="Book a movie and your tickets will show up here."
        />
      ) : (
        <div className="booking-list">
          {bookings.map((booking) => (
            <BookingCard key={booking.id} booking={booking} />
          ))}
        </div>
      )}
    </div>
  )
}
