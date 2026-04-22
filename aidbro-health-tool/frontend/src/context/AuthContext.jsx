import { createContext, useContext, useState, useEffect, useCallback } from "react"

const API = "http://localhost:8000/api"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)   // { email, name, role, has_paid }
  const [token, setToken]     = useState(null)
  const [loading, setLoading] = useState(true)

  // ── Restore session from sessionStorage on mount ──────────────────────────
  useEffect(() => {
    const stored = sessionStorage.getItem("aidbro_token")
    const storedUser = sessionStorage.getItem("aidbro_user")
    if (stored && storedUser) {
      setToken(stored)
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  // ── Save session ──────────────────────────────────────────────────────────
  const saveSession = useCallback((tokenVal, userVal) => {
    setToken(tokenVal)
    setUser(userVal)
    sessionStorage.setItem("aidbro_token", tokenVal)
    sessionStorage.setItem("aidbro_user", JSON.stringify(userVal))
  }, [])

  // ── Register ──────────────────────────────────────────────────────────────
  const register = useCallback(async (email, password, name = "") => {
    const res = await fetch(`${API}/auth/register`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ email, password, name }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Registration failed")
    saveSession(data.access_token, data.user)
    return data
  }, [saveSession])

  // ── Login ─────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const res = await fetch(`${API}/auth/login`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "Login failed")
    saveSession(data.access_token, data.user)
    return data
  }, [saveSession])

  // ── Handle Google OAuth callback (called from AuthCallbackPage) ───────────
  const handleGoogleCallback = useCallback((params) => {
    const userObj = {
      email:    params.get("email"),
      name:     params.get("name") || "",
      role:     "client",
      has_paid: params.get("has_paid") === "true",
    }
    saveSession(params.get("token"), userObj)
    return userObj
  }, [saveSession])

  // ── Logout ────────────────────────────────────────────────────────────────
  const logout = useCallback(() => {
    setUser(null)
    setToken(null)
    sessionStorage.removeItem("aidbro_token")
    sessionStorage.removeItem("aidbro_user")
  }, [])

  // ── Auth fetch helper (attaches token automatically) ──────────────────────
  const authFetch = useCallback(async (url, options = {}) => {
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        "Content-Type":  "application/json",
        "Authorization": token ? `Bearer ${token}` : "",
      },
    })
  }, [token])

  // ── Update has_paid flag after successful payment ─────────────────────────
  const markPaid = useCallback(() => {
    setUser((prev) => {
      if (!prev) return prev
      const updated = { ...prev, has_paid: true }
      sessionStorage.setItem("aidbro_user", JSON.stringify(updated))
      return updated
    })
  }, [])

  const value = {
    user, token, loading,
    register, login, logout,
    handleGoogleCallback,
    authFetch, markPaid,
    isAuthenticated: !!user,
    isPaid:          user?.has_paid === true,
    isAdmin:         user?.role !== "client",
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider")
  return ctx
}
