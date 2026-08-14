import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { fetchShowtime } from '../api/cinemas'
import { processPayment } from '../api/booking'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { ErrorBanner, LoadingScreen, Spinner } from '../components/ui/Feedback'

function useCountdown(expiresAt) {
  const [remaining, setRemaining] = useState(() => Math.max(0, Math.floor((new Date(expiresAt) - Date.now()) / 1000)))
  useEffect(() => {
    const timer = setInterval(() => {
      setRemaining(Math.max(0, Math.floor((new Date(expiresAt) - Date.now()) / 1000)))
    }, 1000)
    return () => clearInterval(timer)
  }, [expiresAt])
  return remaining
}

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function Checkout() {
  const { token } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [lock] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem(`lock_${token}`) || 'null')
    } catch {
      return null
    }
  })
  const [showtime, setShowtime] = useState(null)
  const [loadingShowtime, setLoadingShowtime] = useState(Boolean(lock))
  const [paying, setPaying] = useState(false)
  const [error, setError] = useState('')
  const paidRef = useRef(false)

  const lockExpired = useMemo(() => (lock ? new Date(lock.expires_at) <= Date.now() : true), [lock])
  const remaining = useCountdown(lock?.expires_at)

  useEffect(() => {
    if (!lock) return
    let cancelled = false
    fetchShowtime(lock.showtime_id)
      .then((data) => !cancelled && setShowtime(data))
      .catch(() => {})
      .finally(() => !cancelled && setLoadingShowtime(false))
    return () => {
      cancelled = true
    }
  }, [lock])

  const handlePay = async () => {
    setPaying(true)
    setError('')
    try {
      const result = await processPayment(token, 'mock')
      paidRef.current = true
      sessionStorage.removeItem(`lock_${token}`)
      toast.success('Payment successful!')
      navigate(`/bookings/${result.booking.booking_code}`, { replace: true })
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setPaying(false)
    }
  }

  if (!lock) {
    return (
      <div className="container">
        <div className="card empty-state" style={{ padding: '2rem' }}>
          <span className="icon">⏰</span>
          <h3>Your seat hold has expired</h3>
          <p style={{ color: 'var(--text-muted)' }}>
            We couldn't find an active seat hold for this checkout.
          </p>
          <Link to="/cinemas" className="btn btn-primary mt-2">Browse cinemas</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="section-head">
        <h2 className="section-title">Checkout</h2>
      </div>

      {!lockExpired ? (
        <div className={`lock-timer ${remaining <= 60 ? 'lock-timer-warn' : ''}`}>
          <span className="icon">⏳</span>
          Seats are held for <strong>{formatTime(remaining)}</strong>. Complete payment before they are released.
        </div>
      ) : (
        <div className="lock-timer lock-timer-expired">
          <span className="icon">⏰</span>
          This hold has expired. Please select your seats again.
        </div>
      )}

      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="card checkout-details" style={{ flex: '1 1 380px', padding: '1.5rem' }}>
          <h3>{showtime?.movie || 'Your movie'}</h3>
          {showtime && (
            <>
              <div style={{ color: 'var(--text-muted)' }}>
                🎦 {showtime.cinema}, {showtime.city} · Screen {showtime.screen_name} ({showtime.screen_type_display})
              </div>
              <div style={{ color: 'var(--text-muted)' }}>
                {new Date(`${showtime.show_date}T00:00:00`).toLocaleDateString(undefined, {
                  weekday: 'short', day: 'numeric', month: 'short',
                })} at {showtime.start_time}
              </div>
            </>
          )}
          <div className="divider" />
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Seats</span>
            <div className="rating-big">{lock.seats?.join(', ') || '—'}</div>
          </div>
        </div>

        <div className="card checkout-summary" style={{ flex: '1 1 300px', padding: '1.5rem' }}>
          <h3>Payment summary</h3>
          {lock.price && (
            <div className="price-breakdown">
              <div><span>Subtotal</span><span>₹{Number(lock.price.subtotal).toFixed(2)}</span></div>
              <div><span>Convenience fee</span><span>₹{Number(lock.price.convenience_fee).toFixed(2)}</span></div>
              <div><span>Tax (18%)</span><span>₹{Number(lock.price.tax).toFixed(2)}</span></div>
              <div className="total"><span>Total</span><span>₹{Number(lock.price.total).toFixed(2)}</span></div>
            </div>
          )}
          <ErrorBanner message={error} />
          <button
            className="btn btn-primary btn-block btn-lg mt-2"
            disabled={paying || lockExpired}
            onClick={handlePay}
          >
            {paying ? <Spinner /> : 'Pay now (mock)'}
          </button>
          <p style={{ color: 'var(--text-faint)', fontSize: '0.8rem', marginTop: '0.75rem' }}>
            Demo payment gateway — no real charge. Entering a total ending in .99 fails on purpose for testing.
          </p>
          {loadingShowtime && <LoadingScreen label="Loading details..." />}
        </div>
      </div>
    </div>
  )
}
