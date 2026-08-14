import { api } from './client'

/** List cinemas. Params: search, city, page. */
export async function fetchCinemas(params = {}) {
  const { data } = await api.get('/cinemas/', { params })
  return data
}

/** Cinema detail (by slug). */
export async function fetchCinema(slug) {
  const { data } = await api.get(`/cinemas/${slug}/`)
  return data
}

/** Screens for a cinema. */
export async function fetchScreens(cinemaId) {
  const { data } = await api.get('/screens/', { params: { cinema: cinemaId, page_size: 100 } })
  return data.results || data
}

/** Showtimes, optionally filtered by cinema/date/movie. */
export async function fetchShowtimes(params = {}) {
  const { data } = await api.get('/showtimes/', { params: { ...params, page_size: 100 } })
  return data.results || data
}

/** Single showtime detail (by id). */
export async function fetchShowtime(id) {
  const { data } = await api.get(`/showtimes/${id}/`)
  return data
}

/** Live seat map for a showtime. */
export async function fetchSeatMap(showtimeId) {
  const { data } = await api.get(`/showtimes/${showtimeId}/seats/`)
  return data
}
