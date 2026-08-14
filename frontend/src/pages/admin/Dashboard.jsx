import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchStats } from '../../api/admin'
import { extractError } from '../../api/client'
import { ErrorBanner, LoadingScreen } from '../../components/ui/Feedback'

const STAT_CARDS = [
  { key: 'users', label: 'Users', icon: '👥', to: '/admin/users' },
  { key: 'movies', label: 'Movies', icon: '🎬', to: '/admin/movies' },
  { key: 'cinemas', label: 'Cinemas', icon: '🎦', to: '/admin/cinemas' },
  { key: 'screens', label: 'Screens', icon: '🖥️' },
  { key: 'showtimes', label: 'Showtimes', icon: '🕐', to: '/admin/showtimes' },
  { key: 'bookings', label: 'Bookings', icon: '🎟️', to: '/admin/bookings' },
]

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((err) => setError(extractError(err).message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingScreen label="Loading dashboard..." />
  if (error || !stats) return <ErrorBanner message={error || 'Failed to load stats.'} />

  const { totals, week_revenue, top_movies } = stats
  const maxRevenue = Math.max(1, ...week_revenue.map((d) => d.revenue))

  return (
    <div>
      <div className="section-head">
        <h2 className="section-title">Dashboard</h2>
      </div>

      <ErrorBanner message={error} />

      <div className="stat-grid">
        {STAT_CARDS.map((card) => {
          const inner = (
            <div className="card stat-card">
              <span className="stat-icon">{card.icon}</span>
              <div className="stat-value">{totals[card.key] ?? 0}</div>
              <div className="stat-label">{card.label}</div>
            </div>
          )
          return card.to ? <Link key={card.key} to={card.to} className="stat-link">{inner}</Link> : inner
        })}
        <div className="card stat-card">
          <span className="stat-icon">💰</span>
          <div className="stat-value">₹{Number(totals.revenue || 0).toLocaleString()}</div>
          <div className="stat-label">Total revenue</div>
        </div>
        <div className="card stat-card">
          <span className="stat-icon">📅</span>
          <div className="stat-value">{totals.today_bookings ?? 0}</div>
          <div className="stat-label">Bookings today</div>
        </div>
      </div>

      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="card admin-panel" style={{ flex: '1 1 480px' }}>
          <h3>Revenue — last 7 days</h3>
          <div className="revenue-chart">
            {week_revenue.map((day) => (
              <div key={day.date} className="revenue-bar-wrap">
                <div
                  className="revenue-bar"
                  style={{ height: `${Math.max(4, (day.revenue / maxRevenue) * 120)}px` }}
                  title={`${day.date}: ₹${day.revenue.toFixed(2)}`}
                />
                <span className="revenue-day">
                  {new Date(`${day.date}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short' })}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card admin-panel" style={{ flex: '1 1 320px' }}>
          <h3>Top movies</h3>
          {top_movies.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No bookings yet.</p>
          ) : (
            <ol className="top-movies">
              {top_movies.map((m, i) => (
                <li key={m.title}>
                  <span className="top-movie-rank">{i + 1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="top-movie-title">{m.title}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      {m.bookings} booking{m.bookings !== 1 ? 's' : ''}
                    </div>
                  </div>
                  <strong>₹{Number(m.revenue).toLocaleString()}</strong>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </div>
  )
}
