import { useState } from "react"
import { useAuth } from "../context/AuthContext"
import { useAuditPrice } from "../components/useAuditPrice"
import { GOOGLE_AUTH_URL } from "../config/api"
import SiteLogo from "../components/SiteLogo"

export default function AuthPage({ onSuccess, initialMode = "login" }) {
  const { register, login } = useAuth()
  const { formatted: priceFormatted } = useAuditPrice()
  const [mode, setMode]     = useState(initialMode) // login | register
  const [email, setEmail]   = useState("")
  const [password, setPw]   = useState("")
  const [name, setName]     = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      if (mode === "register") {
        await register(email, password, name)
      } else {
        await login(email, password)
      }
      onSuccess?.()
    } catch (err) {
      setError(err.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">

        {/* Logo */}
        <div className="auth-logo">
          <SiteLogo compact />
        </div>
        <p className="auth-sub">
          {mode === "login"
            ? "Sign in to access your Digital Health report"
            : "Create your account to get started"}
        </p>

        {/* Google OAuth button */}
        <a href={GOOGLE_AUTH_URL} className="btn-google">
          <svg width="18" height="18" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.2l6.7-6.7C35.7 2.5 30.2 0 24 0 14.7 0 6.8 5.4 2.9 13.3l7.8 6.1C12.6 13 17.9 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4 6.9-9.9 7.1-17z"/>
            <path fill="#FBBC05" d="M10.7 28.6c-.5-1.5-.8-3-.8-4.6s.3-3.1.8-4.6l-7.8-6.1C1 16.3 0 20 0 24s1 7.7 2.9 10.7l7.8-6.1z"/>
            <path fill="#34A853" d="M24 48c6.2 0 11.4-2 15.2-5.5l-7.5-5.8c-2.1 1.4-4.7 2.3-7.7 2.3-6.1 0-11.4-4.1-13.3-9.9l-7.8 6.1C6.8 42.6 14.7 48 24 48z"/>
          </svg>
          Continue with Google
        </a>

        <div className="auth-divider">
          <span>or {mode === "login" ? "sign in" : "register"} with email</span>
        </div>

        {/* Email / password form */}
        <form onSubmit={handleSubmit} noValidate>
          {mode === "register" && (
            <div className="auth-field">
              <label>YOUR NAME</label>
              <input
                type="text"
                placeholder="e.g. Rahul Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
          )}
          <div className="auth-field">
            <label>EMAIL ADDRESS *</label>
            <input
              type="email"
              placeholder="you@business.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus={mode === "login"}
            />
          </div>
          <div className="auth-field">
            <label>PASSWORD *</label>
            <input
              type="password"
              placeholder={mode === "register" ? "Min 8 characters" : "Your password"}
              value={password}
              onChange={(e) => setPw(e.target.value)}
              required
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="btn-primary auth-submit" disabled={loading}>
            {loading
              ? "Please wait..."
              : mode === "login" ? "Sign In →" : "Create Account →"}
          </button>
        </form>

        {/* Mode switcher */}
        <p className="auth-switch">
          {mode === "login" ? (
            <>Don't have an account?{" "}
              <button onClick={() => { setMode("register"); setError("") }}>
                Register here
              </button>
            </>
          ) : (
            <>Already have an account?{" "}
              <button onClick={() => { setMode("login"); setError("") }}>
                Sign in
              </button>
            </>
          )}
        </p>

        {/* Info box */}
        <div className="auth-info-box">
          <p>
            <b>🔒 Free to register.</b> After registering, you can purchase
            the Detailed Audit ({priceFormatted}) to
            unlock your full report.
          </p>
        </div>
      </div>
    </div>
  )
}
