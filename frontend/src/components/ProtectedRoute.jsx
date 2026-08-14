import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LoadingScreen } from './ui/Feedback'

/** Blocks access to a page when the user is not logged in. */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingScreen label="Checking your session..." />
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  return children
}

/** Blocks access to auth pages (login/register) when already logged in. */
export function PublicOnlyRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingScreen label="Checking your session..." />
  if (isAuthenticated) return <Navigate to={location.state?.from || '/'} replace />
  return children
}
