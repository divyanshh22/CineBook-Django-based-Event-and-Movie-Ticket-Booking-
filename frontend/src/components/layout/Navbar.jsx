import { useEffect, useRef, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../ui/Toast'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/movies', label: 'Movies' },
  { to: '/events', label: 'Events' },
  { to: '/cinemas', label: 'Cinemas' },
]

export default function Navbar() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    function onClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const handleLogout = async () => {
    setDropdownOpen(false)
    setMenuOpen(false)
    try {
      await logout()
      toast.success('Logged out successfully.')
      navigate('/')
    } catch {
      toast.error('Failed to log out.')
    }
  }

  const initials = (user?.full_name || user?.username || '?')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <NavLink to="/" className="brand">
            <span className="brand-logo">🎬</span>
            Cine<span className="gradient-text">Book</span>
          </NavLink>

          <nav className={`nav-links ${menuOpen ? 'open' : ''}`}>
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="nav-actions">
          {!isAuthenticated ? (
            <>
              <NavLink to="/login" className="btn btn-ghost" onClick={() => setMenuOpen(false)}>
                Log in
              </NavLink>
              <NavLink to="/register" className="btn btn-primary" onClick={() => setMenuOpen(false)}>
                Sign up
              </NavLink>
            </>
          ) : (
            <div className="dropdown" ref={dropdownRef}>
              <button
                className="nav-avatar"
                aria-label="Account menu"
                onClick={() => setDropdownOpen((open) => !open)}
                style={{ border: 'none' }}
              >
                {initials}
              </button>
              {dropdownOpen && (
                <div className="dropdown-menu">
                  <div style={{ padding: '0.5rem 0.8rem' }}>
                    <strong>{user?.full_name || user?.username}</strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{user?.email}</div>
                  </div>
                  <div className="dropdown-sep" />
                  <NavLink to="/profile" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    👤 My profile
                  </NavLink>
                  <NavLink to="/bookings" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    🎟️ My bookings
                  </NavLink>
                  {isAdmin && (
                    <NavLink to="/admin" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                      📊 Admin dashboard
                    </NavLink>
                  )}
                  <div className="dropdown-sep" />
                  <button className="dropdown-item danger" onClick={handleLogout}>
                    ↩️ Log out
                  </button>
                </div>
              )}
            </div>
          )}

          <button
            className="nav-toggle"
            aria-label="Toggle menu"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>
    </header>
  )
}
