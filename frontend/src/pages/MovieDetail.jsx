import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { createReview, fetchMovie, fetchReviews } from '../api/movies'
import { extractError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ui/Toast'
import { Badge, EmptyState, ErrorBanner, LoadingScreen, Spinner } from '../components/ui/Feedback'

function RatingStars({ rating, onSelect }) {
  return (
    <div className="stars" role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((value) => (
        <button
          key={value}
          type="button"
          className={`star ${value <= (rating || 0) ? 'filled' : ''}`}
          onClick={() => onSelect?.(value)}
          disabled={!onSelect}
          aria-label={`${value} star${value > 1 ? 's' : ''}`}
        >
          ★
        </button>
      ))}
    </div>
  )
}

export default function MovieDetail() {
  const { slug } = useParams()
  const { isAuthenticated } = useAuth()
  const toast = useToast()

  const [movie, setMovie] = useState(null)
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [reviewRating, setReviewRating] = useState(0)
  const [reviewComment, setReviewComment] = useState('')
  const [reviewError, setReviewError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [selectedDate, setSelectedDate] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const movieData = await fetchMovie(slug)
      setMovie(movieData)
      const reviewsData = await fetchReviews(movieData.id).catch(() => [])
      setReviews(reviewsData.results || reviewsData)
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    load()
  }, [load])

  const showtimeDates = useMemo(() => Object.keys(movie?.showtimes_by_date || {}).sort(), [movie])

  useEffect(() => {
    if (showtimeDates.length > 0 && !showtimeDates.includes(selectedDate)) {
      setSelectedDate(showtimeDates[0])
    }
  }, [showtimeDates, selectedDate])

  const handleReviewSubmit = async (event) => {
    event.preventDefault()
    setReviewError('')
    setSubmitting(true)
    try {
      const created = await createReview({
        movie: movie.id,
        rating: reviewRating,
        comment: reviewComment.trim(),
      })
      setReviews((prev) => [created, ...prev])
      setReviewRating(0)
      setReviewComment('')
      toast.success('Thanks for your review!')
    } catch (err) {
      setReviewError(extractError(err).message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingScreen label="Loading movie..." />
  if (error) {
    return (
      <div className="container">
        <ErrorBanner message={error} />
        <Link to="/movies" className="btn btn-ghost mt-2">← Back to movies</Link>
      </div>
    )
  }
  if (!movie) return null

  const rating = movie.avg_rating?.average
  const selectedShows = movie.showtimes_by_date?.[selectedDate] || []

  return (
    <div>
      {movie.backdrop && (
        <div
          className="movie-hero"
          style={{ backgroundImage: `linear-gradient(rgba(10,12,19,0.55), var(--bg)), url(${movie.backdrop})` }}
        >
          <div className="container movie-hero-inner">
            <div className="movie-poster movie-poster-lg">
              <img src={movie.poster || '/placeholder-poster.svg'} alt={`${movie.title} poster`} />
            </div>
            <div className="movie-hero-info">
              <div className="row" style={{ gap: '0.4rem' }}>
                <Badge variant="accent">{movie.status === 'now_showing' ? 'Now showing' : 'Upcoming'}</Badge>
                {movie.certification && <Badge>{movie.certification}</Badge>}
              </div>
              <h1 className="movie-hero-title">{movie.title}</h1>
              <div className="movie-hero-meta">
                <span>{movie.language}</span>
                <span>·</span>
                <span>{movie.duration} min</span>
                <span>·</span>
                <span>Released {movie.release_date}</span>
              </div>
              {rating != null ? (
                <div className="movie-hero-rating">
                  <span className="rating-big">★ {Number(rating).toFixed(1)}</span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    {movie.avg_rating?.count} rating{movie.avg_rating?.count !== 1 ? 's' : ''}
                  </span>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)' }}>No ratings yet</div>
              )}
              {movie.genres?.length > 0 && (
                <div className="movie-genres mt-1">
                  {movie.genres.map((genre) => (
                    <span key={genre.id || genre.name}>{genre.name || genre}</span>
                  ))}
                </div>
              )}
              {movie.director && (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.5rem' }}>
                  Directed by <strong>{movie.director}</strong>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="container">
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="movie-detail-main">
            {!movie.backdrop && (
              <div className="row" style={{ alignItems: 'center', gap: '1.5rem' }}>
                <div className="movie-poster movie-poster-lg">
                  <img src={movie.poster || '/placeholder-poster.svg'} alt={`${movie.title} poster`} />
                </div>
                <div>
                  <h1 className="movie-hero-title">{movie.title}</h1>
                  <div className="movie-hero-meta">
                    <span>{movie.language}</span>
                    <span>·</span>
                    <span>{movie.duration} min</span>
                  </div>
                  <div className="row mt-1" style={{ gap: '0.4rem' }}>
                    {movie.genres?.map((genre) => (
                      <Badge key={genre.id || genre.name}>{genre.name || genre}</Badge>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {movie.description && (
              <section className="section">
                <h2 className="section-title">About the movie</h2>
                <p style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>{movie.description}</p>
              </section>
            )}

            {movie.cast?.length > 0 && (
              <section className="section">
                <h2 className="section-title">Cast</h2>
                <div className="cast-grid">
                  {movie.cast.map((actor) => (
                    <div key={actor.id} className="cast-chip">
                      {actor.photo && <img src={actor.photo} alt={actor.name} loading="lazy" />}
                      <span>{actor.name}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="section">
              <h2 className="section-title">Reviews</h2>
              {isAuthenticated ? (
                <form className="card review-form" onSubmit={handleReviewSubmit}>
                  <ErrorBanner message={reviewError} />
                  <label className="field-label">Your rating</label>
                  <RatingStars rating={reviewRating} onSelect={setReviewRating} />
                  <div className="field mt-1">
                    <textarea
                      className="input"
                      rows="3"
                      placeholder="Tell us what you thought..."
                      value={reviewComment}
                      onChange={(e) => setReviewComment(e.target.value)}
                    />
                  </div>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={submitting || reviewRating === 0}
                  >
                    {submitting ? <Spinner /> : 'Submit review'}
                  </button>
                </form>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  <Link to="/login">Log in</Link> to rate and review this movie.
                </p>
              )}

              {reviews.length === 0 ? (
                <EmptyState icon="💬" title="No reviews yet" description="Be the first to review this movie." />
              ) : (
                <div className="review-list mt-2">
                  {reviews.map((review) => (
                    <div key={review.id} className="card review-item">
                      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong>{review.user}</strong>
                        <RatingStars rating={review.rating} />
                      </div>
                      {review.comment && (
                        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>{review.comment}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          <aside className="movie-detail-side">
            <section className="card showtimes-card">
              <h2 className="section-title">Showtimes</h2>
              {showtimeDates.length === 0 ? (
                <EmptyState icon="⏳" title="No shows scheduled" description="Check back soon for showtimes." />
              ) : (
                <>
                  <div className="showtime-dates">
                    {showtimeDates.map((date) => (
                      <button
                        key={date}
                        type="button"
                        className={`date-chip ${date === selectedDate ? 'active' : ''}`}
                        onClick={() => setSelectedDate(date)}
                      >
                        {new Date(`${date}T00:00:00`).toLocaleDateString(undefined, {
                          weekday: 'short',
                          day: 'numeric',
                          month: 'short',
                        })}
                      </button>
                    ))}
                  </div>
                  <div className="showtime-date">
                    <div className="showtime-date-label">
                      {new Date(`${selectedDate}T00:00:00`).toLocaleDateString(undefined, {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'short',
                      })}
                    </div>
                    {selectedShows.length === 0 ? (
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        No shows on this date.
                      </p>
                    ) : (
                      <div className="showtime-times">
                        {selectedShows.map((show) => (
                          <Link
                            key={show.id}
                            to={`/showtimes/${show.id}`}
                            className="showtime-chip"
                            title={`${show.cinema} — Screen ${show.screen} (${show.screen_type})`}
                          >
                            {show.time}
                            <span>₹{Number(show.base_price).toFixed(0)}</span>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.75rem' }}>
                    Pick a showtime to choose your seats.
                  </p>
                </>
              )}
            </section>
          </aside>
        </div>
      </div>
    </div>
  )
}
