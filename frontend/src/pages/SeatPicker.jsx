import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { fetchSeatMap, fetchShowtime } from '../api/cinemas'
import { lockSeats } from '../api/booking'
import { extractError } from '../api/client'
import { useToast } from '../components/ui/Toast'
import { ErrorBanner, LoadingScreen, Spinner } from '../components/ui/Feedback'

const MAX_SEATS = 10

export default function SeatPicker() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [showtime, setShowtime] = useState(null)
  const [seats, setSeats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(new Set())
  const [lockError, setLockError] = useState('')
  const [locking, setLocking] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [stData, seatsData] = await Promise.all([fetchShowtime(id), fetchSeatMap(id)])
      setShowtime(stData)
      setSeats(seatsData)
      // Pre-select seats the user already holds ("mine").
      setSelected(new Set(seatsData.filter((s) => s.state === 'mine').map((s) => s.id)))
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  const rows = useMemo(() => {
    const byRow = new Map()
    for (const seat of seats) {
      if (!byRow.has(seat.row)) byRow.set(seat.row, [])
      byRow.get(seat.row).push(seat)
    }
    return [...byRow.entries()]
  }, [seats])

  const priceBreakdown = useMemo(() => {
    const subtotal = [...selected].reduce((sum, seatId) => {
      const seat = seats.find((s) => s.id === seatId)
      return sum + (seat ? Number(seat.price) : 0)
    }, 0)
    const fee = selected.size > 0 ? 30 : 0
    const tax = selected.size > 0 ? Math.round((subtotal + fee) * 0.18 * 100) / 100 : 0
    return { subtotal, fee, tax, total: Math.round((subtotal + fee + tax) * 100) / 100 }
  }, [selected, seats])

  const toggleSeat = (seat) => {
    if (seat.state === 'booked' || seat.state === 'locked') return
    setLockError('')
    const next = new Set(selected)
    if (next.has(seat.id)) {
      next.delete(seat.id)
    } else {
      if (next.size >= MAX_SEATS) {
        setLockError(`You can select a maximum of ${MAX_SEATS} seats.`)
        return
      }
      next.add(seat.id)
    }
    setSelected(next)
  }

  const handleLock = async () => {
    if (selected.size === 0) return
    setLocking(true)
    setLockError('')
    try {
      const result = await lockSeats(id, [...selected])
      sessionStorage.setItem(
        `lock_${result.token}`,
        JSON.stringify({
          showtime_id: Number(id),
          seats: result.seats,
          price: result.price,
          expires_at: result.expires_at,
        })
      )
      toast.success('Seats locked! Proceed to payment.')
      navigate(`/checkout/${result.token}`)
    } catch (err) {
      const { message, fieldErrors } = extractError(err)
      setLockError(fieldErrors.seat_ids || message)
      await load()
    } finally {
      setLocking(false)
    }
  }

  const seatClass = (seat) => {
    const cls = ['seat']
    if (seat.state === 'booked') cls.push('seat-booked')
    else if (seat.state === 'locked') cls.push('seat-locked')
    else if (selected.has(seat.id)) cls.push('seat-selected')
    else if (seat.state === 'mine') cls.push('seat-mine')
    else cls.push('seat-available')
    if (seat.category === 'vip') cls.push('seat-vip')
    else if (seat.category === 'premium') cls.push('seat-premium')
    return cls.join(' ')
  }

  if (loading) return <LoadingScreen label="Loading seats..." />
  if (error || !showtime) {
    return (
      <div className="container">
        <ErrorBanner message={error || 'Showtime not found.'} />
        <Link to="/cinemas" className="btn btn-ghost mt-2">← Browse cinemas</Link>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="card seat-picker-head">
        <div>
          <h1 className="movie-hero-title">{showtime.movie}</h1>
          <div className="movie-hero-meta">
            <span>🎦 {showtime.cinema}, {showtime.city}</span>
            <span>·</span>
            <span>Screen {showtime.screen_name} ({showtime.screen_type_display})</span>
          </div>
          <div style={{ color: 'var(--text-muted)' }}>
            {new Date(`${showtime.show_date}T00:00:00`).toLocaleDateString(undefined, {
              weekday: 'short', day: 'numeric', month: 'short',
            })} at {showtime.start_time}
          </div>
        </div>
        <div className="text-right">
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Starts at</div>
          <div className="rating-big">₹{Number(showtime.base_price).toFixed(0)}</div>
        </div>
      </div>

      <div className="card seat-map-card">
        <div className="screen-bar">Screen this way</div>

        <div className="seat-legend">
          <span><span className="seat seat-sm seat-available" /> Available</span>
          <span><span className="seat seat-sm seat-selected" /> Selected</span>
          <span><span className="seat seat-sm seat-mine" /> Held by you</span>
          <span><span className="seat seat-sm seat-locked" /> Locked</span>
          <span><span className="seat seat-sm seat-booked" /> Booked</span>
        </div>

        <div className="seat-rows">
          {rows.map(([row, rowSeats]) => (
            <div key={row} className="seat-row">
              <span className="seat-row-label">{row}</span>
              {rowSeats.map((seat) => (
                <button
                  key={seat.id}
                  type="button"
                  className={seatClass(seat)}
                  onClick={() => toggleSeat(seat)}
                  disabled={seat.state === 'booked' || seat.state === 'locked'}
                  title={`${seat.label} — ${seat.category}`}
                  aria-label={`Seat ${seat.label}`}
                >
                  {seat.number}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      <ErrorBanner message={lockError} />

      <div className="card seat-summary">
        <div>
          <strong>Selected: {selected.size === 0 ? 'none' : [...selected].length} seat{selected.size !== 1 ? 's' : ''}</strong>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {selected.size > 0
              ? [...selected].map((s) => seats.find((x) => x.id === s)?.label).sort().join(', ')
              : 'Tap seats on the map to choose them.'}
          </div>
        </div>
        <div className="price-breakdown">
          <div><span>Subtotal</span><span>₹{priceBreakdown.subtotal.toFixed(2)}</span></div>
          <div><span>Convenience fee</span><span>₹{priceBreakdown.fee.toFixed(2)}</span></div>
          <div><span>Tax (18%)</span><span>₹{priceBreakdown.tax.toFixed(2)}</span></div>
          <div className="total"><span>Total</span><span>₹{priceBreakdown.total.toFixed(2)}</span></div>
        </div>
        <button
          className="btn btn-primary btn-lg"
          disabled={selected.size === 0 || locking}
          onClick={handleLock}
        >
          {locking ? <Spinner /> : `Continue to payment · ₹${priceBreakdown.total.toFixed(2)}`}
        </button>
      </div>
    </div>
  )
}
