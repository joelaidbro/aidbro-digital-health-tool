import { useEffect, useState } from "react"

import { API } from "../../src/config/api"

export default function AnonymousSearches({
  token,
  refreshKey,
  selectedSearchId,
  onSelectSearch,
  onUnauthorized,
}) {
  const [search, setSearch] = useState("")
  const [minScore, setMinScore] = useState("")
  const [hasContact, setHasContact] = useState("")
  const [data, setData] = useState({ searches: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const fetchSearches = async () => {
      setLoading(true)
      setError("")
      try {
        const params = new URLSearchParams()
        if (search.trim()) params.set("search", search.trim())
        if (minScore) params.set("min_score", minScore)
        if (hasContact) params.set("has_contact", hasContact)

        const res = await fetch(`${API}/admin/anonymous-searches?${params.toString()}`, {
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
          throw new Error(payload.detail || "Could not load anonymous searches")
        }
        if (!cancelled) {
          setData(payload)
          if (!selectedSearchId && payload.searches?.length) {
            onSelectSearch?.(payload.searches[0].id)
          }
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load anonymous searches")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchSearches()
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, search, minScore, hasContact, selectedSearchId, onSelectSearch, onUnauthorized])

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>Anonymous Searches</h3>
          <p>{data.total || 0} unregistered searches matched</p>
        </div>
      </div>

      <div className="admin-toolbar">
        <input
          className="admin-input"
          placeholder="Search business, location, category, website, email"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <input
          className="admin-input admin-input-small"
          placeholder="Min score"
          value={minScore}
          onChange={(event) => setMinScore(event.target.value.replace(/[^\d]/g, ""))}
        />
        <select className="admin-select" value={hasContact} onChange={(event) => setHasContact(event.target.value)}>
          <option value="">All contacts</option>
          <option value="true">Has contact</option>
          <option value="false">No contact</option>
        </select>
        <div className="admin-muted" style={{ alignSelf: "center" }}>
          Auto-captured from Google, website crawl, or manual patch-up
        </div>
      </div>

      {loading && <div className="admin-table-empty">Loading anonymous searches...</div>}
      {error && <div className="admin-table-empty admin-error-text">{error}</div>}

      {!loading && !error && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Business</th>
                <th>Score</th>
                <th>Contact</th>
                <th>Upgrade</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.searches?.map((row) => (
                <tr
                  key={row.id}
                  className={selectedSearchId === row.id ? "active" : ""}
                  onClick={() => onSelectSearch?.(row.id)}
                >
                  <td>
                    <div className="admin-table-title">{row.business_name}</div>
                    <div className="admin-table-sub">{row.location} · {row.category || "General Business"}</div>
                  </td>
                  <td>
                    <span className="admin-score-chip">{row.total_score ?? "—"}</span>
                  </td>
                  <td>
                    <div className="admin-table-sub">
                      {row.auto_email || row.auto_phone || row.manual_contact_email || row.manual_contact_phone || "No contact captured"}
                    </div>
                  </td>
                  <td>
                    <span className="admin-status-chip">
                      {row.linked_audit_job ? row.linked_audit_job.audit_status : "Not purchased"}
                    </span>
                  </td>
                  <td>{row.created_at ? new Date(row.created_at).toLocaleDateString("en-IN") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!data.searches?.length && (
            <div className="admin-table-empty">No anonymous searches matched the current filters.</div>
          )}
        </div>
      )}
    </section>
  )
}
