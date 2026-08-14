import { api } from './client'

/** Lock seats for a showtime. Returns { token, expires_at, seats, price }. */
export async function lockSeats(showtimeId, seatIds) {
  const { data } = await api.post('/bookings/lock/', { showtime: showtimeId, seat_ids: seatIds })
  return data
}

/** Price preview without locking. Returns { seats, price }. */
export async function previewPrice(showtimeId, seatIds) {
  const { data } = await api.post('/bookings/price/', { showtime: showtimeId, seat_ids: seatIds })
  return data
}

/** Process (mock) payment for a lock. */
export async function processPayment(lockToken, method = 'mock') {
  const { data } = await api.post('/payments/process/', { lock_token: lockToken, method })
  return data
}

/** Current user's bookings. filter = 'upcoming' | 'past' | undefined. */
export async function fetchMyBookings(filter) {
  const params = filter ? { filter } : {}
  const { data } = await api.get('/bookings/', { params })
  return data
}

export async function fetchBooking(code) {
  const { data } = await api.get(`/bookings/${code}/`)
  return data
}

export async function cancelBooking(code) {
  const { data } = await api.post(`/bookings/${code}/cancel/`)
  return data
}

/** Download URL for the printable ticket (PNG). */
export function ticketUrl(code) {
  return `/api/bookings/${code}/ticket/`
}
