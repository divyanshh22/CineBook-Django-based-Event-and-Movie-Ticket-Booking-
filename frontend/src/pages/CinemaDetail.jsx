import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchCinema, fetchScreens, fetchShowtimes } from '../api/cinemas'
import { extractError } from '../api/client'
import { Badge, EmptyState, ErrorBanner, LoadingScreen } from '../components/ui/Feedback'

function formatDateLabel(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`)
  return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })
}

export default function CinemaDetail() {
  const { slug } = useParams()
  const [cinema, setCinema] = useState(null)
  const [screens, setScreens] = useState([])
  const [showtimes, setShowtimes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDate, setSelectedDate] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const cinemaData = await fetchCinema(slug)
      setCinema(cinemaData)
      const [screensData, showtimesData] = await Promise.all([
        fetchScreens(cinemaData.id).catch(() => []),
        fetchShowtimes({ cinema: cinemaData.id }).catch(() => []),
      ])
      setScreens(screensData)
      setShowtimes(showtimesData)

      const dates = [...new Set(showtimesData.map((s) => s.show_date))].sort()
      setSelectedDate((current) => (dates.length > 0 && !dates.includes(current) ? dates[0] : current))
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    load()
  }, [load])

  const dates = useMemo(() => [...new Set(showtimes.map((s) => s.show_date))].sort(), [showtimes])

  const dayShowtimes = useMemo(
    () => showtimes.filter((s) => s.show_date === selectedDate),
    [showtimes, selectedDate]
  )

  const showsByScreen = useMemo(() => {
    const map = new Map()
    for (const s of dayShowtimes) {
      if (!map.has(s.screen_id)) map.set(s.screen_id, [])
      map.get(s.screen_id).push(s)
    }
    return map
  }, [dayShowtimes])

  if (loading) return <LoadingScreen label="Loading cinema..." />
  if (error || !cinema) {
    return (
      <div className="container">
        <ErrorBanner message={error || 'Cinema not found.'} />
        <Link to="/cinemas" className="btn btn-ghost mt-2">← Back to cinemas</Link>
      </div>
    )
  }

  return (
    <div className="container">
      <Link to="/cinemas" className="btn btn-ghost">← All cinemas</Link>

      <div className="card cinema-header mt-2">
        <div>
          <h1 className="movie-hero-title">{cinema.name}</h1>
          <div className="movie-hero-meta">
            <span>📍 {cinema.city}{cinema.state ? `, ${cinema.state}` : ''}</span>
            {cinema.contact_number && <span>· ☎️ {cinema.contact_number}</span>}
            <span>· {cinema.screen_count} screen{cinema.screen_count !== 1 ? 's' : ''}</span>
          </div>
          {cinema.address && <p style={{ color: 'var(--text-muted)' }}>{cinema.address}</p>}
          {cinema.amenities_list?.length > 0 && (
            <div className="movie-genres mt-1">
              {cinema.amenities_list.map((a) => (
                <span key={a}>{a}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      <section className="section">
        <h2 className="section-title">Showtimes</h2>

        {dates.length > 0 && (
          <div className="showtime-dates">
            {dates.map((date) => (
              <button
                key={date}
                type="button"
                className={`date-chip ${date === selectedDate ? 'active' : ''}`}
                onClick={() => setSelectedDate(date)}
              >
                {formatDateLabel(date)}
              </button>
            ))}
          </div>
        )}

        {dates.length === 0 ? (
          <EmptyState icon="⏳" title="No showtimes scheduled" description="Check back soon for showtimes." />
        ) : (
          <div className="screen-shows">
            {screens.map((screen) => {
              const shows = showsByScreen.get(screen.id) || []
              return (
                <div key={screen.id} className="card screen-show-card">
                  <div className="screen-show-head">
                    <div>
                      <strong>{screen.name}</strong>
                      <Badge variant="accent" style={{ marginLeft: '0.5rem' }}>{screen.screen_type_display}</Badge>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {screen.seat_count} seats
                    </span>
                  </div>
                  {shows.length === 0 ? (
                    <p style={{ color: 'var(--text-faint)', fontSize: '0.9rem', margin: 0 }}>
                      No shows on this day.
                    </p>
                  ) : (
                    <div className="showtime-times mt-1">
                      {shows.map((show) => (
                        <Link
                          key={show.id}
                          to={`/showtimes/${show.id}`}
                          className="showtime-chip"
                          title={`${show.movie} — select seats`}
                        >
                          {show.start_time}
                          <span>₹{Number(show.base_price).toFixed(0)}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                  {shows.length > 0 && (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.6rem' }}>
                      Now playing: {shows[0].movie}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
