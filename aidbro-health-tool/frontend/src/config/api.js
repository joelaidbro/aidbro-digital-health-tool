const apiBase =
  (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/+$/, "")

export const API = apiBase
export const GOOGLE_AUTH_URL = `${API}/auth/google`
