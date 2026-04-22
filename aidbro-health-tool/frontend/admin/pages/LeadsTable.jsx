import { useEffect, useState } from "react"

const API = "http://localhost:8000/api"

export default function LeadsTable({
  token,
  refreshKey,
  selectedLeadId,
  onSelectLead,
  onUnauthorized,
}) {
  const [status, setStatus] = useState("")
  const [minScore, setMinScore] = useState("")
  const [hasContact, setHasContact] = useState("")
  const [search, setSearch] = useState("")
  const [data, setData] = useState({ leads: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const fetchLeads = async () => {
      setLoading(true)
      setError("")
      try {
        const params = new URLSearchParams()
        if (status) params.set("status", status)
        if (minScore) params.set("min_score", minScore)
        if (hasContact) params.set("has_contact", hasContact)
        if (search.trim()) params.set("search", search.trim())

        const res = await fetch(`${API}/admin/leads?${params.toString()}`, {
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
          throw new Error(payload.detail || "Could not load leads")
        }
        if (!cancelled) {
          setData(payload)
          if (!selectedLeadId && payload.leads?.length) {
            onSelectLead?.(payload.leads[0].id)
          }
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load leads")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchLeads()
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, status, minScore, hasContact, search, onSelectLead, selectedLeadId, onUnauthorized])

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>Lead Pipeline</h3>
          <p>{data.total || 0} leads matched</p>
        </div>
      </div>

      <div className="admin-toolbar">
        <input
          className="admin-input"
          placeholder="Search business, location, category, email"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select className="admin-select" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="demo_done">Demo done</option>
          <option value="stage4_paid">Stage 4 paid</option>
          <option value="service_signed">Service signed</option>
          <option value="not_interested">Not interested</option>
          <option value="follow_up">Follow up</option>
        </select>
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
      </div>

      {loading && <div className="admin-table-empty">Loading leads...</div>}
      {error && <div className="admin-table-empty admin-error-text">{error}</div>}

      {!loading && !error && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Business</th>
                <th>Score</th>
                <th>Status</th>
                <th>Contact</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.leads?.map((lead) => (
                <tr
                  key={lead.id}
                  className={selectedLeadId === lead.id ? "active" : ""}
                  onClick={() => onSelectLead?.(lead.id)}
                >
                  <td>
                    <div className="admin-table-title">{lead.business_name}</div>
                    <div className="admin-table-sub">{lead.location} · {lead.category || "General Business"}</div>
                  </td>
                  <td>
                    <span className="admin-score-chip">{lead.total_score ?? "—"}</span>
                  </td>
                  <td>
                    <span className="admin-status-chip">{lead.status}</span>
                  </td>
                  <td>
                    <div className="admin-table-sub">
                      {lead.contact_email || lead.contact_phone || "No contact captured"}
                    </div>
                  </td>
                  <td>{lead.created_at ? new Date(lead.created_at).toLocaleDateString("en-IN") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!data.leads?.length && (
            <div className="admin-table-empty">No leads matched the current filters.</div>
          )}
        </div>
      )}
    </section>
  )
}
