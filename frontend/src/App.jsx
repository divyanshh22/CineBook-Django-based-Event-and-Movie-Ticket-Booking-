import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './components/ui/Toast'
import Layout from './components/layout/Layout'
import { ProtectedRoute, PublicOnlyRoute } from './components/ProtectedRoute'
import Home from './pages/Home'
import Movies from './pages/Movies'
import MovieDetail from './pages/MovieDetail'
import Cinemas from './pages/Cinemas'
import CinemaDetail from './pages/CinemaDetail'
import SeatPicker from './pages/SeatPicker'
import Checkout from './pages/Checkout'
import MyBookings from './pages/MyBookings'
import BookingDetail from './pages/BookingDetail'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Profile from './pages/Profile'
import ComingSoon from './pages/ComingSoon'
import AdminLayout from './pages/admin/AdminLayout'
import AdminDashboard from './pages/admin/Dashboard'
import AdminMovies from './pages/admin/Movies'
import AdminCinemas from './pages/admin/Cinemas'
import AdminShowtimes from './pages/admin/Showtimes'
import AdminBookings from './pages/admin/Bookings'
import AdminUsers from './pages/admin/Users'

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Home />} />
              <Route path="/movies" element={<Movies />} />
              <Route path="/movies/:slug" element={<MovieDetail />} />
              <Route path="/events" element={<ComingSoon title="Events" description="Concerts, plays and live shows are on their way." />} />
              <Route path="/cinemas" element={<Cinemas />} />
              <Route path="/cinemas/:slug" element={<CinemaDetail />} />
              <Route
                path="/showtimes/:id"
                element={
                  <ProtectedRoute>
                    <SeatPicker />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/checkout/:token"
                element={
                  <ProtectedRoute>
                    <Checkout />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <Profile />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/bookings"
                element={
                  <ProtectedRoute>
                    <MyBookings />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/bookings/:code"
                element={
                  <ProtectedRoute>
                    <BookingDetail />
                  </ProtectedRoute>
                }
              />

              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<AdminDashboard />} />
                <Route path="movies" element={<AdminMovies />} />
                <Route path="cinemas" element={<AdminCinemas />} />
                <Route path="showtimes" element={<AdminShowtimes />} />
                <Route path="bookings" element={<AdminBookings />} />
                <Route path="users" element={<AdminUsers />} />
              </Route>
            </Route>

            <Route
              path="/login"
              element={
                <PublicOnlyRoute>
                  <Layout />
                </PublicOnlyRoute>
              }
            >
              <Route path="" element={<Login />} />
            </Route>

            <Route
              path="/register"
              element={
                <PublicOnlyRoute>
                  <Layout />
                </PublicOnlyRoute>
              }
            >
              <Route path="" element={<Register />} />
            </Route>

            <Route path="/forgot-password" element={<Layout />}>
              <Route path="" element={<ForgotPassword />} />
            </Route>

            <Route path="/reset-password" element={<Layout />}>
              <Route path="" element={<ResetPassword />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
