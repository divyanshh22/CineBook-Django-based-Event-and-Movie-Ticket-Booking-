import { useCallback, useEffect, useState } from 'react'
import { adminMovies, adminScreens, adminShowtimes } from '../../api/admin'
import { extractError } from '../../api/client'
import { ErrorBanner, LoadingScreen } from '../../components/ui/Feedback'

const STATUS_OPTIONS = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'active', label: 'Active' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'completed', label: 'Completed' },
]

const EMPTY_FORM = {
  screen: '',
  movie: '',
  show_date: '',
  start_time: '',
  end_time: '',
  base_price: 200,
  status: 'scheduled',
}

export default function Showtimes() {
  const [showtimes, setShowtimes] = useState([])
  const [movies, setMovies] = useState([])
  const [screens, setScreens] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    Promise.all([adminShowtimes.list(), adminMovies.list(), adminScreens.list()])
      .then(([st, m, s]) => {
        setShowtimes(st)
        setMovies(m)
        setScreens(s)
      })
      .catch((err) => setError(extractError(err).message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  const movieTitle = (id) => movies.find((m) => m.id === id)?.title || id
  const screenLabel = (id) => {
    const s = screens.find((x) => x.id === id)
    return s ? `${s.name}` : id
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      if (editing.id) {
        await adminShowtimes.update(editing.id, editing)
      } else {
        await adminShowtimes.create(editing)
      }
      setEditing(null)
      load()
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setSaving(false)
    }
  }

  const setStatus = async (showtime, status) => {
    if (status === 'cancelled') {
      const ok = window.confirm(
        `Cancel showtime #${showtime.id}? This releases all active seat locks for it.`
      )
      if (!ok) return
    }
    try {
      await adminShowtimes.update(showtime.id, { status })
      load()
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  if (loading && showtimes.length === 0) return <LoadingScreen label="Loading showtimes..." />

  return (
    <div>
      <div className="section-head">
        <h2 className="section-title">Showtimes</h2>
        <button className="btn btn-primary" onClick={() => setEditing({ ...EMPTY_FORM, id: null })}>+ Add showtime</button>
      </div>

      <ErrorBanner message={error} />

      <div className="card admin-panel table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Movie</th>
              <th>Screen</th>
              <th>Date</th>
              <th>Time</th>
              <th>Base price</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {showtimes.length === 0 && (
              <tr><td colSpan="8" style={{ color: 'var(--text-muted)' }}>No showtimes yet.</td></tr>
            )}
            {showtimes.map((st) => (
              <tr key={st.id}>
                <td>{st.id}</td>
                <td>{movieTitle(st.movie)}</td>
                <td>{screenLabel(st.screen)}</td>
                <td>{st.show_date}</td>
                <td>{st.start_time} – {st.end_time}</td>
                <td>₹{st.base_price}</td>
                <td><span className={`badge badge-${st.status}`}>{st.status}</span></td>
                <td className="admin-actions">
                  {st.status !== 'cancelled' && (
                    <button className="btn btn-sm btn-danger" onClick={() => setStatus(st, 'cancelled')}>Cancel</button>
                  )}
                  <button className="btn btn-sm" onClick={() => setEditing({ ...st, screen: st.screen, movie: st.movie })}>Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editing.id ? 'Edit showtime' : 'Add showtime'}</h3>
            <div className="form-grid">
              <label className="form-field">
                Movie *
                <select value={editing.movie} onChange={(e) => setEditing({ ...editing, movie: Number(e.target.value) })}>
                  <option value="">Select movie</option>
                  {movies.map((m) => <option key={m.id} value={m.id}>{m.title}</option>)}
                </select>
              </label>
              <label className="form-field">
                Screen *
                <select value={editing.screen} onChange={(e) => setEditing({ ...editing, screen: Number(e.target.value) })}>
                  <option value="">Select screen</option>
                  {screens.map((s) => <option key={s.id} value={s.id}>{screenLabel(s.id)}</option>)}
                </select>
              </label>
              <label className="form-field">
                Date *
                <input type="date" value={editing.show_date} onChange={(e) => setEditing({ ...editing, show_date: e.target.value })} />
              </label>
              <label className="form-field">
                Start time *
                <input type="time" value={editing.start_time} onChange={(e) => setEditing({ ...editing, start_time: e.target.value })} />
              </label>
              <label className="form-field">
                End time
                <input type="time" value={editing.end_time || ''} onChange={(e) => setEditing({ ...editing, end_time: e.target.value })} />
              </label>
              <label className="form-field">
                Base price (₹)
                <input type="number" min="1" value={editing.base_price} onChange={(e) => setEditing({ ...editing, base_price: Number(e.target.value) })} />
              </label>
              <label className="form-field">
                Status
                <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value })}>
                  {STATUS_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </label>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={save}
                disabled={saving || !editing.movie || !editing.screen || !editing.show_date || !editing.start_time}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
