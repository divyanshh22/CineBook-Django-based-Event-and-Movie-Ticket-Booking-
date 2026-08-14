import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, fetchCsrfToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/session/')
      setUser(data.user)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = useCallback(async (username, password) => {
    const { data } = await api.post('/auth/login/', { username, password })
    setUser(data.user)
    return data
  }, [])

  const register = useCallback(async (payload) => {
    const { data } = await api.post('/auth/register/', payload)
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout/')
    } finally {
      setUser(null)
    }
  }, [])

  const updateProfile = useCallback(async (payload) => {
    const { data } = await api.patch('/auth/me/', payload)
    setUser(data)
    return data
  }, [])

  const changePassword = useCallback(async (payload) => {
    await api.post('/auth/password/change/', payload)
    setUser(null)
  }, [])

  const requestPasswordReset = useCallback(async (email) => {
    const { data } = await api.post('/auth/password/reset/', { email })
    return data
  }, [])

  const confirmPasswordReset = useCallback(async (payload) => {
    const { data } = await api.post('/auth/password/reset/confirm/', payload)
    return data
  }, [])

  // Ensure a CSRF cookie exists before the first state-changing call.
  useEffect(() => {
    if (!document.cookie.includes('csrftoken')) fetchCsrfToken()
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      isAdmin: Boolean(user?.is_staff),
      login,
      register,
      logout,
      updateProfile,
      changePassword,
      requestPasswordReset,
      confirmPasswordReset,
      refreshUser,
    }),
    [user, loading, login, register, logout, updateProfile, changePassword, requestPasswordReset, confirmPasswordReset, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
