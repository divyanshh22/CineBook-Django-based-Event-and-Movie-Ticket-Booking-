import { Navigate, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { LoadingScreen } from '../../components/ui/Feedback'

const ADMIN_LINKS = [
  { to: '/admin', label: 'Dashboard', icon: '📊', end: true },
  { to: '/admin/movies', label: 'Movies', icon: '🎬' },
  { to: '/admin/cinemas', label: 'Cinemas & screens', icon: '🎦' },
  { to: '/admin/showtimes', label: 'Showtimes', icon: '🕐' },
  { to: '/admin/bookings', label: 'Bookings', icon: '🎟️' },
  { to: '/admin/users', label: 'Users', icon: '👥' },
]

export default function AdminLayout() {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingScreen label="Checking your session..." />
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  if (!isAdmin) return <Navigate to="/" replace />

  return (
    <div className="container">
      <div className="admin-layout">
        <aside className="admin-sidebar">
          <h3 className="admin-sidebar-title">CineBook Admin</h3>
          <nav className="admin-nav">
            {ADMIN_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
              >
                <span>{link.icon}</span>
                {link.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
