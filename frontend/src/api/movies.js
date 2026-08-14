import { api } from './client'

/** List movies. Accepts query params: search, genre, status, ordering, page. */
export async function fetchMovies(params = {}) {
  const { data } = await api.get('/movies/', { params })
  return data
}

/** Full movie detail including showtimes grouped by date. */
export async function fetchMovie(slug) {
  const { data } = await api.get(`/movies/${slug}/`)
  return data
}

export async function fetchGenres() {
  const { data } = await api.get('/genres/')
  return data
}

export async function fetchReviews(movieId) {
  const { data } = await api.get('/reviews/', { params: { movie: movieId } })
  return data
}

export async function createReview(payload) {
  const { data } = await api.post('/reviews/', payload)
  return data
}
