import { useEffect, useState } from "react"

import { API } from "../../src/config/api"

export default function UsersTable({
  token,
  refreshKey,
  selectedUserId,
  onSelectUser,
  onUnauthorized,
}) {
  const [search, setSearch] = useState("")
  const [provider, setProvider] = useState("")
  const [hasPaid, setHasPaid] = useState("")
  const [data, setData] = useState({ users: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const fetchUsers = async () => {
      setLoading(true)
      setError("")
      try {
        const params = new URLSearchParams()
        if (search.trim()) params.set("search", search.trim())
        if (provider) params.set("provider", provider)
        if (hasPaid) params.set("has_paid", hasPaid)

        const res = await fetch(`${API}/admin/users?${params.toString()}`, {
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
          throw new Error(payload.detail || "Could not load users")
        }
        if (!cancelled) {
          setData(payload)
          if (!selectedUserId && payload.users?.length) {
            onSelectUser?.(payload.users[0].id, { openDetail: false })
          }
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load users")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchUsers()
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, search, provider, hasPaid, selectedUserId, onSelectUser, onUnauthorized])

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>Registered Users</h3>
          <p>{data.total || 0} account records matched</p>
        </div>
      </div>

      <div className="admin-toolbar">
        <input
          className="admin-input"
          placeholder="Search email or name"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select className="admin-select" value={provider} onChange={(event) => setProvider(event.target.value)}>
          <option value="">All providers</option>
          <option value="email">Email</option>
          <option value="google">Google</option>
        </select>
        <select className="admin-select" value={hasPaid} onChange={(event) => setHasPaid(event.target.value)}>
          <option value="">All payment states</option>
          <option value="true">Has paid audit</option>
          <option value="false">No paid audit</option>
        </select>
        <div className="admin-muted" style={{ alignSelf: "center" }}>
          Search history and audit jobs are now tracked per account
        </div>
      </div>

      {loading && <div className="admin-table-empty">Loading users...</div>}
      {error && <div className="admin-table-empty admin-error-text">{error}</div>}

      {!loading && !error && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Provider</th>
                <th>Searches</th>
                <th>Paid Audits</th>
                <th>Last Login</th>
              </tr>
            </thead>
            <tbody>
              {data.users?.map((user) => (
                <tr
                  key={user.id}
                  className={selectedUserId === user.id ? "active" : ""}
                  onClick={() => onSelectUser?.(user.id, { openDetail: true })}
                >
                  <td>
                    <div className="admin-table-title">{user.name || user.email}</div>
                    <div className="admin-table-sub">{user.email}</div>
                  </td>
                  <td>
                    <span className="admin-status-chip">{user.auth_provider || "email"}</span>
                  </td>
                  <td>
                    <span className="admin-score-chip">{user.search_count ?? 0}</span>
                  </td>
                  <td>
                    <span className="admin-score-chip">{user.audit_count ?? 0}</span>
                  </td>
                  <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleDateString("en-IN") : "Never"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!data.users?.length && (
            <div className="admin-table-empty">No registered users matched the current filters.</div>
          )}
        </div>
      )}
    </section>
  )
}
