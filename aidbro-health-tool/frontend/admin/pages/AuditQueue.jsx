import { useEffect, useState } from "react"

const API = "http://localhost:8000/api"

export default function AuditQueue({
  token,
  refreshKey,
  selectedAuditId,
  onSelectAudit,
  onUnauthorized,
}) {
  const [status, setStatus] = useState("")
  const [audits, setAudits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const fetchQueue = async () => {
      setLoading(true)
      setError("")
      try {
        const params = new URLSearchParams()
        if (status) params.set("status", status)

        const res = await fetch(`${API}/admin/audits?${params.toString()}`, {
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
          throw new Error(payload.detail || "Could not load audit queue")
        }
        if (!cancelled) {
          setAudits(payload.audits || [])
          if (!selectedAuditId && payload.audits?.length) {
            onSelectAudit?.(payload.audits[0].client.id)
          }
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load audit queue")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchQueue()
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, status, onUnauthorized, onSelectAudit, selectedAuditId])

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>Paid Audit Queue</h3>
          <p>{audits.length} paid clients in the current view</p>
        </div>
      </div>

      <div className="admin-toolbar">
        <select className="admin-select" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In progress</option>
          <option value="review">Review</option>
          <option value="completed">Completed</option>
          <option value="delivered">Delivered</option>
        </select>
      </div>

      {loading && <div className="admin-table-empty">Loading audit queue...</div>}
      {error && <div className="admin-table-empty admin-error-text">{error}</div>}

      {!loading && !error && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Client</th>
                <th>Status</th>
                <th>Open</th>
                <th>Paid</th>
                <th>Report</th>
              </tr>
            </thead>
            <tbody>
              {audits.map((row) => (
                <tr
                  key={row.client.id}
                  className={selectedAuditId === row.client.id ? "active" : ""}
                  onClick={() => onSelectAudit?.(row.client.id)}
                >
                  <td>
                    <div className="admin-table-title">{row.lead?.business_name || row.client.email}</div>
                    <div className="admin-table-sub">{row.client.email}</div>
                  </td>
                  <td>
                    <span className="admin-status-chip">{row.client.audit_status}</span>
                  </td>
                  <td>{row.open_days} day(s)</td>
                  <td>{row.client.paid_at ? new Date(row.client.paid_at).toLocaleDateString("en-IN") : "—"}</td>
                  <td>{row.report_approved ? "Approved" : "In progress"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!audits.length && (
            <div className="admin-table-empty">No paid audits matched this status.</div>
          )}
        </div>
      )}
    </section>
  )
}
