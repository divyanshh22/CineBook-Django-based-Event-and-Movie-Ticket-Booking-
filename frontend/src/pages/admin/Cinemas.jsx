import { useCallback, useEffect, useState } from 'react'
import { adminCinemas, adminScreens } from '../../api/admin'
import { extractError } from '../../api/client'
import { ErrorBanner, LoadingScreen } from '../../components/ui/Feedback'

const SCREEN_TYPES = [
  { value: 'standard', label: 'Standard' },
  { value: 'imax', label: 'IMAX' },
  { value: 'dolby', label: 'Dolby Atmos' },
  { value: 'platinum', label: 'Platinum' },
  { value: 'screenx', label: 'ScreenX' },
  { value: 'vip', label: 'VIP Lounge' },
]

const EMPTY_CINEMA = {
  name: '',
  city: '',
  state: '',
  address: '',
  contact_number: '',
  amenities: '',
  is_active: true,
}

const EMPTY_SCREEN = { cinema: '', name: '', screen_type: 'standard', rows: 10, columns: 12 }

const EMPTY_LAYOUT = { screen: '', rows: 10, columns: 12, base_price: 200, premium_rows: 2, vip_rows: 0 }

export default function Cinemas() {
  const [cinemas, setCinemas] = useState([])
  const [screens, setScreens] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editCinema, setEditCinema] = useState(null)
  const [editScreen, setEditScreen] = useState(null)
  const [layout, setLayout] = useState(null)
  const [expanded, setExpanded] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    Promise.all([adminCinemas.list(), adminScreens.list()])
      .then(([c, s]) => {
        setCinemas(c)
        setScreens(s)
      })
      .catch((err) => setError(extractError(err).message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  const saveCinema = async () => {
    try {
      if (editCinema.id) await adminCinemas.update(editCinema.id, editCinema)
      else await adminCinemas.create(editCinema)
      setEditCinema(null)
      load()
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  const removeCinema = async (cinema) => {
    if (!window.confirm(`Delete "${cinema.name}"? Its screens and showtimes will be removed.`)) return
    try {
      await adminCinemas.remove(cinema.id)
      if (expanded === cinema.id) setExpanded(null)
      load()
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  const saveScreen = async () => {
    try {
      if (editScreen.id) await adminScreens.update(editScreen.id, editScreen)
      else await adminScreens.create(editScreen)
      setEditScreen(null)
      load()
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  const removeScreen = async (screen) => {
    if (!window.confirm(`Delete screen "${screen.name}"?`)) return
    try {
      await adminScreens.remove(screen.id)
      load()
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  const generateLayout = async () => {
    try {
      const res = await adminScreens.layout(layout)
      alert(res.detail)
      setLayout(null)
    } catch (err) {
      setError(extractError(err).message)
    }
  }

  const screensOf = (cinemaId) => screens.filter((s) => s.cinema === cinemaId)

  if (loading && cinemas.length === 0) return <LoadingScreen label="Loading cinemas..." />

  return (
    <div>
      <div className="section-head">
        <h2 className="section-title">Cinemas</h2>
        <button className="btn btn-primary" onClick={() => setEditCinema({ ...EMPTY_CINEMA, id: null })}>+ Add cinema</button>
      </div>

      <ErrorBanner message={error} />

      {cinemas.length === 0 && (
        <div className="card admin-panel"><p style={{ color: 'var(--text-muted)' }}>No cinemas yet.</p></div>
      )}

      {cinemas.map((cinema) => (
        <div className="card admin-panel admin-cinema" key={cinema.id}>
          <div className="admin-cinema-head">
            <div>
              <h3 style={{ marginBottom: '0.25rem' }}>
                {cinema.name} {!cinema.is_active && <span className="badge badge-ended">inactive</span>}
              </h3>
              <div className="admin-sub">
                {cinema.city}, {cinema.state} · {cinema.contact_number || 'no phone'}
              </div>
              {cinema.amenities && <div className="admin-sub">{cinema.amenities}</div>}
            </div>
            <div className="admin-actions">
              <button className="btn btn-sm" onClick={() => { setExpanded(expanded === cinema.id ? null : cinema.id); setEditScreen({ ...EMPTY_SCREEN, cinema: cinema.id }) }}>
                {expanded === cinema.id ? 'Close screens' : 'Screens & seats'}
              </button>
              <button className="btn btn-sm" onClick={() => setEditCinema({ ...cinema })}>Edit</button>
              <button className="btn btn-sm btn-danger" onClick={() => removeCinema(cinema)}>Delete</button>
            </div>
          </div>

          {expanded === cinema.id && (
            <div className="admin-screens">
              {screensOf(cinema.id).length === 0 && (
                <p style={{ color: 'var(--text-muted)' }}>No screens — add one below.</p>
              )}
              {screensOf(cinema.id).map((screen) => (
                <div key={screen.id} className="admin-screen-row">
                  <div>
                    <strong>{screen.name}</strong>
                    <span className="admin-sub">
                      {' '}· {SCREEN_TYPES.find((t) => t.value === screen.screen_type)?.label} · {screen.rows}×{screen.columns}
                    </span>
                  </div>
                  <div className="admin-actions">
                    <button className="btn btn-sm" onClick={() => setEditScreen({ ...screen })}>Edit</button>
                    <button className="btn btn-sm" onClick={() => setLayout({ ...EMPTY_LAYOUT, screen: screen.id })}>Generate seats</button>
                    <button className="btn btn-sm btn-danger" onClick={() => removeScreen(screen)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {editCinema && (
        <div className="modal-overlay" onClick={() => setEditCinema(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editCinema.id ? 'Edit cinema' : 'Add cinema'}</h3>
            <div className="form-grid">
              <label className="form-field">Name *<input value={editCinema.name} onChange={(e) => setEditCinema({ ...editCinema, name: e.target.value })} /></label>
              <label className="form-field">City *<input value={editCinema.city} onChange={(e) => setEditCinema({ ...editCinema, city: e.target.value })} /></label>
              <label className="form-field">State<input value={editCinema.state} onChange={(e) => setEditCinema({ ...editCinema, state: e.target.value })} /></label>
              <label className="form-field">Contact<input value={editCinema.contact_number} onChange={(e) => setEditCinema({ ...editCinema, contact_number: e.target.value })} /></label>
              <label className="form-field form-field-wide">Address<input value={editCinema.address} onChange={(e) => setEditCinema({ ...editCinema, address: e.target.value })} /></label>
              <label className="form-field form-field-wide">Amenities (comma separated)<input value={editCinema.amenities} onChange={(e) => setEditCinema({ ...editCinema, amenities: e.target.value })} placeholder="Parking, Food court, Recliners" /></label>
              <label className="form-field form-field-wide form-check">
                <input type="checkbox" checked={editCinema.is_active} onChange={(e) => setEditCinema({ ...editCinema, is_active: e.target.checked })} /> Active
              </label>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setEditCinema(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={saveCinema} disabled={!editCinema.name.trim() || !editCinema.city.trim()}>Save</button>
            </div>
          </div>
        </div>
      )}

      {editScreen && (
        <div className="modal-overlay" onClick={() => setEditScreen(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editScreen.id ? 'Edit screen' : 'Add screen'}</h3>
            <div className="form-grid">
              <label className="form-field">Cinema
                <select value={editScreen.cinema} onChange={(e) => setEditScreen({ ...editScreen, cinema: Number(e.target.value) })}>
                  {cinemas.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </label>
              <label className="form-field">Name *<input value={editScreen.name} onChange={(e) => setEditScreen({ ...editScreen, name: e.target.value })} /></label>
              <label className="form-field">Type
                <select value={editScreen.screen_type} onChange={(e) => setEditScreen({ ...editScreen, screen_type: e.target.value })}>
                  {SCREEN_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </label>
              <label className="form-field">Rows<input type="number" min="1" max="26" value={editScreen.rows} onChange={(e) => setEditScreen({ ...editScreen, rows: Number(e.target.value) })} /></label>
              <label className="form-field">Columns<input type="number" min="1" max="30" value={editScreen.columns} onChange={(e) => setEditScreen({ ...editScreen, columns: Number(e.target.value) })} /></label>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setEditScreen(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={saveScreen} disabled={!editScreen.name.trim()}>Save</button>
            </div>
          </div>
        </div>
      )}

      {layout && (
        <div className="modal-overlay" onClick={() => setLayout(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Generate seat layout</h3>
            <p className="admin-sub">
              Rebuilds all seats for this screen. Existing bookings keep their seats (booked seats will be recreated as booked),
              but locks are dropped.
            </p>
            <div className="form-grid">
              <label className="form-field">Screen
                <select value={layout.screen} onChange={(e) => setLayout({ ...layout, screen: Number(e.target.value) })}>
                  {screens.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </label>
              <label className="form-field">Base price (₹)<input type="number" min="1" value={layout.base_price} onChange={(e) => setLayout({ ...layout, base_price: Number(e.target.value) })} /></label>
              <label className="form-field">Rows<input type="number" min="1" max="26" value={layout.rows} onChange={(e) => setLayout({ ...layout, rows: Number(e.target.value) })} /></label>
              <label className="form-field">Columns<input type="number" min="1" max="30" value={layout.columns} onChange={(e) => setLayout({ ...layout, columns: Number(e.target.value) })} /></label>
              <label className="form-field">Premium rows<input type="number" min="0" max="26" value={layout.premium_rows} onChange={(e) => setLayout({ ...layout, premium_rows: Number(e.target.value) })} /></label>
              <label className="form-field">VIP rows<input type="number" min="0" max="26" value={layout.vip_rows} onChange={(e) => setLayout({ ...layout, vip_rows: Number(e.target.value) })} /></label>
            </div>
            <div className="modal-actions">
              <button className="btn" onClick={() => setLayout(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={generateLayout}>Generate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
