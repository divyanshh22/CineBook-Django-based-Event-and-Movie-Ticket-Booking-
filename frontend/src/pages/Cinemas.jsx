import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCinemas } from '../api/cinemas'
import { extractError } from '../api/client'
import { EmptyState, ErrorBanner, LoadingScreen } from '../components/ui/Feedback'

function CinemaCard({ cinema }) {
  return (
    <Link to={`/cinemas/${cinema.slug}`} className="card cinema-card">
      {cinema.image && (
        <div className="cinema-card-image">
          <img src={cinema.image} alt={`${cinema.name} exterior`} loading="lazy" />
        </div>
      )}
      <div className="cinema-card-body">
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem' }}>
          <h3 className="cinema-card-title">{cinema.name}</h3>
          <span className="screen-count-badge">
            {cinema.screen_count} screen{cinema.screen_count !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="cinema-card-meta">
          <span>📍 {cinema.city}{cinema.state ? `, ${cinema.state}` : ''}</span>
        </div>
        {cinema.address && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.35rem 0' }}>
            {cinema.address}
          </p>
        )}
        {cinema.amenities_list?.length > 0 && (
          <div className="movie-genres mt-1">
            {cinema.amenities_list.map((amenity) => (
              <span key={amenity}>{amenity}</span>
            ))}
          </div>
        )}
      </div>
    </Link>
  )
}

export default function Cinemas() {
  const [cinemas, setCinemas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [city, setCity] = useState('')
  const [cities, setCities] = useState([])
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page }
      if (search.trim()) params.search = search.trim()
      if (city) params.city = city
      const data = await fetchCinemas(params)
      setCinemas(data.results || data)
      setPagination({
        count: data.count ?? data.length,
        next: data.next,
        previous: data.previous,
      })
      const seen = new Set()
      setCities(
        (data.results || data)
          .filter((c) => !seen.has(c.city) && seen.add(c.city))
          .map((c) => c.city)
      )
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [page, search, city])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="container">
      <div className="section-head">
        <h2 className="section-title">Cinemas</h2>
      </div>

      <div className="movie-filters">
        <input
          type="search"
          className="input"
          placeholder="Search cinemas by name or address..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
        />
        <select
          className="input"
          value={city}
          onChange={(e) => {
            setCity(e.target.value)
            setPage(1)
          }}
        >
          <option value="">All cities</option>
          {cities.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingScreen label="Loading cinemas..." />
      ) : cinemas.length === 0 ? (
        <EmptyState icon="🎦" title="No cinemas found" description="Try a different search or city." />
      ) : (
        <>
          <div className="cinema-list">
            {cinemas.map((cinema) => (
              <CinemaCard key={cinema.id} cinema={cinema} />
            ))}
          </div>

          <div className="row center mt-3" style={{ justifyContent: 'center', gap: '0.5rem' }}>
            <button
              className="btn btn-ghost"
              disabled={!pagination.previous}
              onClick={() => setPage((p) => p - 1)}
            >
              ← Previous
            </button>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Page {page}
            </span>
            <button
              className="btn btn-ghost"
              disabled={!pagination.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  )
}
