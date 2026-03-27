'use client'

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { API_BASE } from './api'

interface User {
  id: string
  email: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  handleOAuthTokens: (accessToken: string, refreshToken: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  loginWithGoogle: async () => {},
  handleOAuthTokens: async () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Validate token on mount
  useEffect(() => {
    const stored = localStorage.getItem('testara_token')
    if (!stored) {
      setLoading(false)
      return
    }
    setToken(stored)

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${stored}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Invalid token')
        return res.json()
      })
      .then((data) => {
        setUser(data)
      })
      .catch(() => {
        localStorage.removeItem('testara_token')
        localStorage.removeItem('testara_refresh_token')
        setToken(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => null)
      throw new Error(err?.detail || 'Login failed')
    }
    const data = await res.json()
    localStorage.setItem('testara_token', data.session.access_token)
    localStorage.setItem('testara_refresh_token', data.session.refresh_token)
    setToken(data.session.access_token)
    setUser(data.user)
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => null)
      throw new Error(err?.detail || 'Registration failed')
    }
    const data = await res.json()
    if (data.session?.access_token) {
      localStorage.setItem('testara_token', data.session.access_token)
      localStorage.setItem('testara_refresh_token', data.session.refresh_token)
      setToken(data.session.access_token)
      setUser(data.user)
    }
  }, [])

  const loginWithGoogle = useCallback(async () => {
    const res = await fetch(`${API_BASE}/auth/google/url`)
    if (!res.ok) throw new Error('Failed to get Google sign-in URL')
    const data = await res.json()
    // Redirect to Supabase → Google → callback
    window.location.href = data.url
  }, [])

  const handleOAuthTokens = useCallback(async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('testara_token', accessToken)
    localStorage.setItem('testara_refresh_token', refreshToken)
    setToken(accessToken)

    // Fetch user info
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (res.ok) {
      const data = await res.json()
      setUser(data)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('testara_token')
    localStorage.removeItem('testara_refresh_token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, loginWithGoogle, handleOAuthTokens, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
