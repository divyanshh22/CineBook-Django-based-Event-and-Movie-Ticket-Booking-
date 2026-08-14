import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { cancelBooking, fetchBooking, ticketUrl } from '../api/booking'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { Badge, ErrorBanner, LoadingScreen, Spinner } from '../components/ui/Feedback'

export default function BookingDetail() {
  const { code } = useParams()
  const toast = useToast()

  const [booking, setBooking] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cancelling, setCancelling] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setBooking(await fetchBooking(code))
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [code])

  useEffect(() => {
    load()
  }, [load])

  const handleCancel = async () => {
    if (!window.confirm('Cancel this booking? Seats will be released and the payment refunded.')) return
    setCancelling(true)
    try {
      await cancelBooking(code)
      toast.success('Booking cancelled.')
      await load()
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setCancelling(false)
    }
  }

  if (loading) return <LoadingScreen label="Loading booking..." />
  if (error || !booking) {
    return (
      <div className="container">
        <ErrorBanner message={error || 'Booking not found.'} />
        <Link to="/bookings" className="btn btn-ghost mt-2">← My bookings</Link>
      </div>
    )
  }

  const confirmed = booking.status === 'confirmed'

  return (
    <div className="container">
      <Link to="/bookings" className="btn btn-ghost">← My bookings</Link>

      <div className={`ticket ${confirmed ? '' : 'ticket-cancelled'}`}>
        <div className="ticket-accent" />
        <div className="ticket-body">
          <div className="ticket-header">
            <span className="brand-logo">🎬</span>
            <strong>Cine<span className="gradient-text">Book</span></strong>
            <Badge variant={confirmed ? 'success' : 'danger'}>
              {booking.status_display}
            </Badge>
          </div>

          <h1 className="ticket-movie">{booking.movie}</h1>

          <div className="ticket-grid">
            <div>
              <div className="ticket-label">Cinema</div>
              <div>{booking.cinema}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{booking.cinema_city}</div>
            </div>
            <div>
              <div className="ticket-label">Screen</div>
              <div>{booking.screen} ({booking.screen_type})</div>
            </div>
            <div>
              <div className="ticket-label">Date</div>
              <div>
                {new Date(`${booking.show_date}T00:00:00`).toLocaleDateString(undefined, {
                  weekday: 'short', day: 'numeric', month: 'short',
                })}
              </div>
            </div>
            <div>
              <div className="ticket-label">Time</div>
              <div>{booking.start_time}</div>
            </div>
          </div>

          <div className="ticket-seats">
            <div className="ticket-label">Seats</div>
            <div className="ticket-seat-labels">
              {booking.seats.map((s) => (
                <span key={s.seat} className="ticket-seat-chip">{s.seat}</span>
              ))}
            </div>
          </div>

          <div className="divider" />

          <div className="ticket-footer">
            <div>
              <div className="ticket-label">Booking ID</div>
              <code>{booking.booking_code}</code>
            </div>
            <div>
              <div className="ticket-label">Total paid</div>
              <div className="ticket-total">₹{Number(booking.total).toFixed(2)}</div>
            </div>
            {booking.payment_status && (
              <div>
                <div className="ticket-label">Payment</div>
                <div>{booking.payment_status}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {confirmed && (
        <div className="row mt-2">
          <a className="btn btn-primary btn-lg" href={ticketUrl(code)}>
            ⬇️ Download ticket (QR)
          </a>
          <button className="btn btn-danger" onClick={handleCancel} disabled={cancelling}>
            {cancelling ? <Spinner /> : 'Cancel booking'}
          </button>
        </div>
      )}

      <ErrorBanner message={error} />
    </div>
  )
}
