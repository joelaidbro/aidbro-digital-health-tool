import { useEffect, useState } from "react"

import { API } from "../../src/config/api"

export default function TeamManagement({ token, refreshKey, onSaved, onUnauthorized }) {
  const [admins, setAdmins] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "analyst",
  })

  useEffect(() => {
    let cancelled = false

    const fetchTeam = async () => {
      setLoading(true)
      setError("")
      try {
        const res = await fetch(`${API}/admin/team`, {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        })
        if (res.status === 401 || res.status === 403) {
          onUnauthorized?.()
          return
        }
        const payload = await res.json()
        if (!res.ok) {
          throw new Error(payload.detail || "Could not load team")
        }
        if (!cancelled) {
          setAdmins(payload.admins || [])
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load team")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchTeam()
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, onUnauthorized])

  const handleCreate = async (event) => {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const res = await fetch(`${API}/admin/team`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      })
      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.()
        return
      }
      const payload = await res.json()
      if (!res.ok) {
        throw new Error(payload.detail || "Could not create admin account")
      }
      setForm({ name: "", email: "", password: "", role: "analyst" })
      setMessage("Admin user created successfully.")
      onSaved?.()
    } catch (createError) {
      setError(createError.message || "Could not create admin account")
    }
  }

  const handlePatch = async (adminId, patch) => {
    setError("")
    setMessage("")
    try {
      const res = await fetch(`${API}/admin/team/${adminId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(patch),
      })
      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.()
        return
      }
      const payload = await res.json()
      if (!res.ok) {
        throw new Error(payload.detail || "Could not update admin account")
      }
      setMessage("Admin account updated.")
      onSaved?.()
    } catch (patchError) {
      setError(patchError.message || "Could not update admin account")
    }
  }

  return (
    <div className="admin-dashboard">
      <section className="admin-panel-card">
        <div className="admin-section-header">
          <div>
            <h3>Create Team Member</h3>
            <p>Super admins can provision analysts and managers here.</p>
          </div>
        </div>

        <form className="admin-form-grid admin-form-grid-four" onSubmit={handleCreate}>
          <label className="admin-field">
            <span>Name</span>
            <input
              className="admin-input"
              value={form.name}
              onChange={(event) => setForm((value) => ({ ...value, name: event.target.value }))}
              required
            />
          </label>
          <label className="admin-field">
            <span>Email</span>
            <input
              className="admin-input"
              type="email"
              value={form.email}
              onChange={(event) => setForm((value) => ({ ...value, email: event.target.value }))}
              required
            />
          </label>
          <label className="admin-field">
            <span>Password</span>
            <input
              className="admin-input"
              type="password"
              value={form.password}
              onChange={(event) => setForm((value) => ({ ...value, password: event.target.value }))}
              required
            />
          </label>
          <label className="admin-field">
            <span>Role</span>
            <select
              className="admin-select"
              value={form.role}
              onChange={(event) => setForm((value) => ({ ...value, role: event.target.value }))}
            >
              <option value="analyst">Analyst</option>
              <option value="manager">Manager</option>
              <option value="super_admin">Super Admin</option>
            </select>
          </label>
          <div className="admin-actions">
            <button className="btn-primary" type="submit">Create Admin User</button>
          </div>
        </form>
      </section>

      <section className="admin-panel-card">
        <div className="admin-section-header">
          <div>
            <h3>Current Team</h3>
            <p>{admins.length} internal accounts</p>
          </div>
        </div>

        {loading && <div className="admin-table-empty">Loading team members...</div>}
        {error && <div className="admin-inline-message error">{error}</div>}
        {message && <div className="admin-inline-message success">{message}</div>}

        {!loading && (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Last login</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((admin) => (
                  <tr key={admin.id}>
                    <td>
                      <div className="admin-table-title">{admin.name}</div>
                      <div className="admin-table-sub">{admin.email}</div>
                    </td>
                    <td>
                      <select
                        className="admin-select"
                        value={admin.role}
                        onChange={(event) => handlePatch(admin.id, { role: event.target.value })}
                      >
                        <option value="analyst">Analyst</option>
                        <option value="manager">Manager</option>
                        <option value="super_admin">Super Admin</option>
                      </select>
                    </td>
                    <td>{admin.last_login_at ? new Date(admin.last_login_at).toLocaleString("en-IN") : "Never"}</td>
                    <td>{admin.is_active ? "Active" : "Inactive"}</td>
                    <td>
                      <button
                        className="btn-ghost"
                        onClick={() => handlePatch(admin.id, { is_active: !admin.is_active })}
                      >
                        {admin.is_active ? "Deactivate" : "Reactivate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!admins.length && (
              <div className="admin-table-empty">No admin users have been created yet.</div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
