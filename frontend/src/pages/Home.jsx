import { Link } from 'react-router-dom'

/**
 * Placeholder home page for Phase 1.
 * Phase 2 will replace the "coming soon" sections with real data
 * (trending/upcoming movies, cinemas, events, categories).
 */
export default function Home() {
  return (
    <div className="container">
      <section className="hero">
        <h1>
          Your movies, events &amp; cinemas — <span className="gradient-text">one tap away.</span>
        </h1>
        <p>
          Discover the latest releases, book showtimes, pick your seats and carry your tickets in your pocket.
        </p>
        <div className="row" style={{ gap: '0.75rem' }}>
          <Link to="/movies" className="btn btn-primary btn-lg">Explore movies</Link>
          <Link to="/events" className="btn btn-secondary btn-lg">Browse events</Link>
        </div>
      </section>

      <section className="section mt-3">
        <div className="section-head">
          <h2 className="section-title">Explore</h2>
        </div>
        <div className="row">
          <Link to="/movies" className="card" style={{ flex: '1 1 300px', padding: '1.5rem' }}>
            <h3>🎬 Movies</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Now showing and upcoming releases with full details, ratings, cast and showtimes.
            </p>
          </Link>
          <Link to="/cinemas" className="card" style={{ flex: '1 1 300px', padding: '1.5rem' }}>
            <h3>🎦 Cinemas &amp; showtimes</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Browse cinemas, screens and daily showtimes for your favourite movies.
            </p>
          </Link>
          <Link to="/events" className="card" style={{ flex: '1 1 300px', padding: '1.5rem' }}>
            <h3>🎪 Events</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Concerts, plays and more with categories, venues and ticket options.
            </p>
          </Link>
        </div>
      </section>
    </div>
  )
}
