import { useCallback, useEffect, useState } from 'react'
import { adminActors, adminGenres, adminMovies } from '../../api/admin'
import { extractError } from '../../api/client'
import { ErrorBanner, LoadingScreen } from '../../components/ui/Feedback'

const STATUS_OPTIONS = [
  { value: 'now_showing', label: 'Now showing' },
  { value: 'upcoming', label: 'Coming soon' },
  { value: 'archived', label: 'Ended' },
]

const EMPTY_FORM = {
  title: '',
  description: '',
  duration: '',
  release_date: '',
  language: '',
  certification: '',
  director: '',
  status: 'now_showing',
  trending: false,
  genre_ids: [],
  cast_ids: [],
}

function buildMovieFormData(data, file) {
  const fd = new FormData()
  Object.entries(data).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return
    if (key === 'poster' || key === 'backdrop') return
    if (Array.isArray(value)) value.forEach((v) => fd.append(key, v))
    else fd.append(key, value)
  })
  if (file) fd.append('poster', file)
  return fd
}

export default function Movies() {
  const [movies, setMovies] = useState([])
  const [genres, setGenres] = useState([])
  const [actors, setActors] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)
  const [posterFile, setPosterFile] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    Promise.all([adminMovies.list(), adminGenres.list(), adminActors.list()])
      .then(([m, g, a]) => {
        setMovies(m)
        setGenres(g)
        setActors(a)
      })
      .catch((err) => setError(extractError(err).message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  const openCreate = () => {
    setPosterFile(null)
    setEditing({ ...EMPTY_FORM, id: null })
  }
  const openEdit = (movie) => {
    setPosterFile(null)
    setEditing({
      ...movie,
      duration: movie.duration,
      release_date: movie.release_date || '',
      genre_ids: movie.genre_ids || [],
      cast_ids: movie.cast_ids || [],
    })
  }

  const close = () => {
    setEditing(null)
    setPosterFile(null)
    setError('')
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const payload = posterFile ? buildMovieFormData(editing, posterFile) : editing
      if (editing.id) {
        await adminMovies.update(editing.id, payload)
      } else {
        await adminMovies.create(payload)
      }
      close()
      load()
    } catch (err) {
      setError(extractError(err).message)
    } finally {
      setSaving(false)
    }
  }

  const remove = async (movie) => {
    if (!window.confirm(`Delete "${movie.title}"? This cannot be undone.`)) return
    try {
      await adminMovies.remove(movie.id)
      load()
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  const toggleIds = (key, id) => {
    const current = editing[key]
    setEditing({
      ...editing,
      [key]: current.includes(id) ? current.filter((v) => v !== id) : [...current, id],
    })
  }

  const setField = (key, value) => setEditing({ ...editing, [key]: value })

  if (loading && movies.length === 0) return <LoadingScreen label="Loading movies..." />

  return (
    <div>
      <div className="section-head">
        <h2 className="section-title">Movies</h2>
        <button className="btn btn-primary" onClick={openCreate}>+ Add movie</button>
      </div>

      <ErrorBanner message={error} />

      <div className="card admin-panel table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Poster</th>
              <th>Title</th>
              <th>Status</th>
              <th>Genre</th>
              <th>Duration</th>
              <th>Release</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {movies.length === 0 && (
              <tr><td colSpan="7" style={{ color: 'var(--text-muted)' }}>No movies yet.</td></tr>
            )}
            {movies.map((movie) => (
              <tr key={movie.id}>
                <td>
                  {movie.poster ? (
                    <img src={movie.poster} alt={movie.title} className="admin-thumb" />
                  ) : (
                    <div className="admin-thumb admin-thumb-empty">🎬</div>
                  )}
                </td>
                <td>
                  <strong>{movie.title}</strong>
                  <div className="admin-sub">{movie.director} · {movie.language}</div>
                </td>
                <td><span className={`badge badge-${movie.status}`}>{movie.status.replace('_', ' ')}</span></td>
                <td>{(movie.genres || []).join(', ') || '—'}</td>
                <td>{movie.duration} min</td>
                <td>{movie.release_date}</td>
                <td className="admin-actions">
                  <button className="btn btn-sm" onClick={() => openEdit(movie)}>Edit</button>
                  <button className="btn btn-sm btn-danger" onClick={() => remove(movie)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="modal-overlay" onClick={close}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editing.id ? 'Edit movie' : 'Add movie'}</h3>
            <div className="form-grid">
              <label className="form-field">
                Title *
                <input value={editing.title} onChange={(e) => setField('title', e.target.value)} placeholder="Movie title" />
              </label>
              <label className="form-field">
                Director
                <input value={editing.director} onChange={(e) => setField('director', e.target.value)} placeholder="Director name" />
              </label>
              <label className="form-field">
                Duration (min)
                <input type="number" min="1" value={editing.duration} onChange={(e) => setField('duration', e.target.value)} />
              </label>
              <label className="form-field">
                Release date
                <input type="date" value={editing.release_date} onChange={(e) => setField('release_date', e.target.value)} />
              </label>
              <label className="form-field">
                Language
                <input value={editing.language} onChange={(e) => setField('language', e.target.value)} placeholder="Hindi" />
              </label>
              <label className="form-field">
                Certification
                <input value={editing.certification} onChange={(e) => setField('certification', e.target.value)} placeholder="U/A" />
              </label>
              <label className="form-field">
                Status
                <select value={editing.status} onChange={(e) => setField('status', e.target.value)}>
                  {STATUS_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </label>
              <label className="form-field">
                Trailer URL
                <input value={editing.trailer_url || ''} onChange={(e) => setField('trailer_url', e.target.value)} placeholder="https://youtu.be/..." />
              </label>
              <label className="form-field">
                Poster image
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setPosterFile(e.target.files[0] || null)}
                />
              </label>
              {posterFile && (
                <div className="form-field form-field-wide">
                  New poster preview
                  <img src={URL.createObjectURL(posterFile)} alt="New poster preview" className="poster-upload-preview" />
                </div>
              )}
              <label className="form-field form-field-wide">
                Description
                <textarea rows="3" value={editing.description} onChange={(e) => setField('description', e.target.value)} />
              </label>
              <label className="form-field form-field-wide">
                Genres
                <div className="chip-picker">
                  {genres.map((g) => (
                    <button
                      key={g.id}
                      type="button"
                      className={`chip ${editing.genre_ids.includes(g.id) ? 'chip-on' : ''}`}
                      onClick={() => toggleIds('genre_ids', g.id)}
                    >
                      {g.name}
                    </button>
                  ))}
                  {genres.length === 0 && <span style={{ color: 'var(--text-muted)' }}>No genres — add via Django admin.</span>}
                </div>
              </label>
              <label className="form-field form-field-wide">
                Cast
                <div className="chip-picker">
                  {actors.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      className={`chip ${editing.cast_ids.includes(a.id) ? 'chip-on' : ''}`}
                      onClick={() => toggleIds('cast_ids', a.id)}
                    >
                      {a.name}
                    </button>
                  ))}
                  {actors.length === 0 && <span style={{ color: 'var(--text-muted)' }}>No actors — add via Django admin.</span>}
                </div>
              </label>
              <label className="form-field form-field-wide form-check">
                <input
                  type="checkbox"
                  checked={editing.trending}
                  onChange={(e) => setField('trending', e.target.checked)}
                />
                Trending
              </label>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={close}>Cancel</button>
              <button className="btn btn-primary" onClick={save} disabled={saving || !editing.title.trim()}>
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
