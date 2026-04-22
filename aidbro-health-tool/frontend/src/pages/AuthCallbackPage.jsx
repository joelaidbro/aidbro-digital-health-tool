import { useEffect } from "react"
import { useAuth } from "../context/AuthContext"

/**
 * Google OAuth redirects to /auth/callback?token=...&email=...&name=...
 * This page reads those params, saves the session, then redirects to portal.
 */
export default function AuthCallbackPage({ onComplete }) {
  const { handleGoogleCallback } = useAuth()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const error  = params.get("error")

    if (error) {
      console.error("Google OAuth error:", error)
      onComplete?.("error")
      return
    }

    const token = params.get("token")
    if (token) {
      const user = handleGoogleCallback(params)
      // Clean up URL
      window.history.replaceState({}, "", window.location.pathname)
      onComplete?.("success", user)
    } else {
      onComplete?.("error")
    }
  }, [])

  return (
    <div className="auth-page">
      <div className="auth-card" style={{ textAlign: "center" }}>
        <div className="loading-orb" style={{ margin: "0 auto 20px" }} />
        <h3 style={{ fontFamily: "var(--font-head)", marginBottom: 8 }}>
          Completing sign in...
        </h3>
        <p style={{ color: "var(--gray)", fontSize: 14 }}>
          Just a moment while we set up your account.
        </p>
      </div>
    </div>
  )
}
