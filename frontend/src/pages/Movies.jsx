import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchGenres, fetchMovies } from '../api/movies'
import { extractError } from '../api/client'
import { Badge, EmptyState, ErrorBanner, LoadingScreen } from '../components/ui/Feedback'

function posterUrl(poster) {
  return poster || '/placeholder-poster.svg'
}

function MovieCard({ movie }) {
  return (
    <Link to={`/movies/${movie.slug}`} className="movie-card">
      <div className="movie-poster">
        <img src={posterUrl(movie.poster)} alt={`${movie.title} poster`} loading="lazy" />
        {movie.rating != null && (
          <span className="movie-rating">
            ★ {Number(movie.rating).toFixed(1)}
          </span>
        )}
        {movie.status === 'upcoming' && <Badge variant="warning">Upcoming</Badge>}
      </div>
      <div className="movie-card-body">
        <h3 className="movie-title">{movie.title}</h3>
        <div className="movie-meta">
          {movie.language} · {movie.duration} min
          {movie.certification && <span className="movie-cert">{movie.certification}</span>}
        </div>
        {movie.genres?.length > 0 && (
          <div className="movie-genres">
            {movie.genres.slice(0, 3).map((genre) => (
              <span key={genre}>{genre}</span>
            ))}
          </div>
        )}
      </div>
    </Link>
  )
}

export default function Movies() {
  const [movies, setMovies] = useState([])
  const [genres, setGenres] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [genre, setGenre] = useState('')
  const [status, setStatus] = useState('')
  const [order, setOrder] = useState('popularity')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, ordering: order }
      if (search.trim()) params.search = search.trim()
      if (genre) params.genre = genre
      if (status) params.status = status
      const data = await fetchMovies(params)
      setMovies(data.results || data)
      setPagination({
        count: data.count ?? data.length,
        next: data.next,
        previous: data.previous,
      })
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [page, search, genre, status, order])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    fetchGenres()
      .then((data) => setGenres(data.results || data))
      .catch(() => {})
  }, [])

  const filtersChanged = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  return (
    <div className="container">
      <div className="section-head">
        <h2 className="section-title">Movies</h2>
      </div>

      <div className="movie-filters">
        <input
          type="search"
          className="input"
          placeholder="Search movies, cast, directors..."
          value={search}
          onChange={(e) => filtersChanged(setSearch)(e.target.value)}
        />
        <select className="input" value={genre} onChange={(e) => filtersChanged(setGenre)(e.target.value)}>
          <option value="">All genres</option>
          {genres.map((g) => (
            <option key={g.id} value={g.slug}>{g.name}</option>
          ))}
        </select>
        <select className="input" value={status} onChange={(e) => filtersChanged(setStatus)(e.target.value)}>
          <option value="">All status</option>
          <option value="now_showing">Now showing</option>
          <option value="upcoming">Upcoming</option>
        </select>
        <select className="input" value={order} onChange={(e) => filtersChanged(setOrder)(e.target.value)}>
          <option value="popularity">Most popular</option>
          <option value="-avg_rating">Highest rated</option>
          <option value="-release_date">Newest</option>
          <option value="title">A–Z</option>
        </select>
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingScreen label="Loading movies..." />
      ) : movies.length === 0 ? (
        <EmptyState
          icon="🎬"
          title="No movies found"
          description="Try adjusting the search or filters."
        />
      ) : (
        <>
          <div className="movie-grid">
            {movies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
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
