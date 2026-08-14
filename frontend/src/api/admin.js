import { api } from './client'

const ADMIN = '/admin'

/** Dashboard stats. */
export async function fetchStats() {
  const { data } = await api.get(`${ADMIN}/stats/`)
  return data
}

/** Generic paginated list. */
async function list(path, params = {}) {
  const { data } = await api.get(`${ADMIN}/${path}/`, { params: { ...params, page_size: 100 } })
  return data.results || data
}

async function create(path, payload) {
  const { data } = await api.post(`${ADMIN}/${path}/`, payload)
  return data
}

async function update(path, id, payload) {
  const { data } = await api.patch(`${ADMIN}/${path}/${id}/`, payload)
  return data
}

async function remove(path, id) {
  await api.delete(`${ADMIN}/${path}/${id}/`)
}

export const adminMovies = {
  list: (params) => list('movies', params),
  create: (payload) => create('movies', payload),
  update: (id, payload) => update('movies', id, payload),
  remove: (id) => remove('movies', id),
}

export const adminCinemas = {
  list: (params) => list('cinemas', params),
  create: (payload) => create('cinemas', payload),
  update: (id, payload) => update('cinemas', id, payload),
  remove: (id) => remove('cinemas', id),
}

export const adminScreens = {
  list: (params) => list('screens', params),
  create: (payload) => create('screens', payload),
  update: (id, payload) => update('screens', id, payload),
  remove: (id) => remove('screens', id),
  layout: (payload) => api.post(`${ADMIN}/seat-layout/`, payload).then((r) => r.data),
}

export const adminShowtimes = {
  list: (params) => list('showtimes', params),
  create: (payload) => create('showtimes', payload),
  update: (id, payload) => update('showtimes', id, payload),
}

export const adminBookings = {
  list: (params) => list('bookings', params),
}

export const adminUsers = {
  list: (params) => list('users', params),
}

export const adminGenres = {
  list: () => list('genres'),
  create: (payload) => create('genres', payload),
}

export const adminActors = {
  list: () => list('actors'),
  create: (payload) => create('actors', payload),
}
