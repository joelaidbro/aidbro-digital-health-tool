import { useState } from "react"

export default function AdminLogin({ loading, error, onLogin }) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = async (event) => {
    event.preventDefault()
    await onLogin({ email, password })
  }

  return (
    <div className="admin-login-page">
      <div className="admin-login-card">
        <div className="admin-login-badge">Internal use only</div>
        <h1>Aidbro Admin Panel</h1>
        <p>
          Sign in with your analyst or manager credentials to review leads, run the
          detailed audit workflow, and approve client reports.
        </p>

        <form className="admin-login-form" onSubmit={handleSubmit}>
          <div className="admin-field">
            <label>WORK EMAIL</label>
            <input
              className="admin-input"
              type="email"
              placeholder="team@aidbro.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="admin-field">
            <label>PASSWORD</label>
            <input
              className="admin-input"
              type="password"
              placeholder="Your admin password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {error && <p className="admin-inline-message error">{error}</p>}

          <button className="btn-primary admin-login-submit" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Enter Admin Workspace →"}
          </button>
        </form>
      </div>
    </div>
  )
}
