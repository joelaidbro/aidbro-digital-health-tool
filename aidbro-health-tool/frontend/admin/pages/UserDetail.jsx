import { useEffect, useMemo, useState } from "react"

import { API } from "../../src/config/api"
import SearchAuditSnapshot from "../components/SearchAuditSnapshot"

function SummaryCard({ label, value }) {
  return (
    <div className="admin-summary-card">
      <div className="admin-summary-label">{label}</div>
      <div className="admin-summary-value">{value || "—"}</div>
    </div>
  )
}

export default function UserDetail({
  token,
  userId,
  refreshKey,
  onBack,
  onOpenAudit,
  onUnauthorized,
}) {
  const [detail, setDetail] = useState(null)
  const [selectedSearchId, setSelectedSearchId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!userId) {
      setDetail(null)
      setSelectedSearchId(null)
      return
    }

    let cancelled = false

    const fetchDetail = async () => {
      setLoading(true)
      setError("")
      try {
        const res = await fetch(`${API}/admin/users/${userId}`, {
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
          throw new Error(payload.detail || "Could not load user detail")
        }
        if (!cancelled) {
          setDetail(payload)
          setSelectedSearchId(payload.searches?.[0]?.id || null)
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load user detail")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchDetail()
    return () => {
      cancelled = true
    }
  }, [token, userId, refreshKey, onUnauthorized])

  const activeSearch = useMemo(
    () => detail?.searches?.find((item) => item.id === selectedSearchId) || detail?.searches?.[0] || null,
    [detail, selectedSearchId],
  )

  if (!userId) {
    return <section className="admin-panel-card admin-placeholder">Select a registered user to inspect account activity and saved searches.</section>
  }

  if (loading) {
    return <section className="admin-panel-card admin-placeholder">Loading user detail...</section>
  }

  if (error && !detail) {
    return <section className="admin-panel-card admin-placeholder admin-error-text">{error}</section>
  }

  const user = detail?.user || {}
  const firstAuditJob = detail?.audit_jobs?.find((job) => job.legacy_client_id)

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>{user.name || user.email || "Registered User"}</h3>
          <p>{user.email || "No email"} · {(user.auth_provider || "email").toUpperCase()} login</p>
        </div>
        <div className="admin-topbar-meta">
          <button className="btn-ghost admin-back-button" type="button" onClick={onBack}>
            ← Back to Registered Users
          </button>
          {firstAuditJob?.legacy_client_id && (
            <button className="btn-primary" onClick={() => onOpenAudit?.(firstAuditJob.legacy_client_id)}>
              Open Paid Audit →
            </button>
          )}
        </div>
      </div>

      <div className="admin-grid admin-grid-three">
        <SummaryCard label="Created" value={user.created_at ? new Date(user.created_at).toLocaleDateString("en-IN") : "—"} />
        <SummaryCard label="Last Login" value={user.last_login_at ? new Date(user.last_login_at).toLocaleDateString("en-IN") : "Never"} />
        <SummaryCard label="Legacy Paid Client" value={detail?.legacy_client ? detail.legacy_client.audit_status : "Not linked"} />
      </div>

      <div className="admin-subsection">
        <h4>Recent searches</h4>
        {!detail?.searches?.length ? (
          <div className="admin-muted">No saved searches yet for this account.</div>
        ) : (
          <div className="admin-chip-row">
            {detail.searches.map((search) => (
              <button
                key={search.id}
                className={`admin-tab ${activeSearch?.id === search.id ? "active" : ""}`}
                onClick={() => setSelectedSearchId(search.id)}
                type="button"
              >
                {search.business_name} · {search.total_score ?? "—"}
              </button>
            ))}
          </div>
        )}
      </div>

      {activeSearch && (
        <>
          <div className="admin-info-list">
            <div><strong>Selected business:</strong> {activeSearch.business_name}</div>
            <div><strong>Location:</strong> {activeSearch.location}</div>
            <div><strong>Website:</strong> {activeSearch.website_url || "Not detected"}</div>
            <div><strong>Submitted phone:</strong> {activeSearch.manual_contact_phone || activeSearch.auto_phone || "Not captured"}</div>
            <div><strong>Detected contact:</strong> {activeSearch.auto_email || "Not captured"}</div>
          </div>

          <SearchAuditSnapshot
            search={activeSearch}
            audit={activeSearch.audit_json || {}}
            title="Selected Search Result"
          />
        </>
      )}

      <div className="admin-grid admin-grid-two">
        <div className="admin-subsection">
          <h4>Paid audit jobs</h4>
          {!detail?.audit_jobs?.length ? (
            <div className="admin-muted">No paid audit jobs yet.</div>
          ) : (
            <div className="admin-stack-list">
              {detail.audit_jobs.map((job) => (
                <div key={job.id} className="admin-stack-item">
                  <div>
                    <div className="admin-table-title">Audit job #{job.id}</div>
                    <div className="admin-table-sub">Status: {job.audit_status}</div>
                  </div>
                  <div className="admin-table-sub">
                    {job.created_at ? new Date(job.created_at).toLocaleDateString("en-IN") : "—"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="admin-subsection">
          <h4>Recent activity</h4>
          {!detail?.activity?.length ? (
            <div className="admin-muted">No activity recorded yet.</div>
          ) : (
            <div className="admin-stack-list">
              {detail.activity.map((item) => (
                <div key={item.id} className="admin-stack-item">
                  <div>
                    <div className="admin-table-title">{item.event_type}</div>
                    <div className="admin-table-sub">
                      {item.created_at ? new Date(item.created_at).toLocaleString("en-IN") : "—"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {error && <div className="admin-inline-message error">{error}</div>}
    </section>
  )
}
