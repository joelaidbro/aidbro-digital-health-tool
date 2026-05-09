import { useEffect, useState } from "react"

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

export default function AnonymousSearchDetail({
  token,
  searchId,
  refreshKey,
  onBack,
  onOpenAudit,
  onUnauthorized,
}) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!searchId) {
      setDetail(null)
      return
    }

    let cancelled = false

    const fetchDetail = async () => {
      setLoading(true)
      setError("")
      try {
        const res = await fetch(`${API}/admin/anonymous-searches/${searchId}`, {
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
          throw new Error(payload.detail || "Could not load search detail")
        }
        if (!cancelled) {
          setDetail(payload)
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load search detail")
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
  }, [token, searchId, refreshKey, onUnauthorized])

  if (!searchId) {
    return <section className="admin-panel-card admin-placeholder">Select an anonymous search to inspect the captured result.</section>
  }

  if (loading) {
    return <section className="admin-panel-card admin-placeholder">Loading search detail...</section>
  }

  if (error && !detail) {
    return <section className="admin-panel-card admin-placeholder admin-error-text">{error}</section>
  }

  const search = detail?.search || {}
  const audit = detail?.audit_json || {}
  const score = audit.score || {}
  const business = audit.business || {}
  const pagespeed = audit.pagespeed || {}
  const linkedAudit = detail?.linked_audit_job

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>{search.business_name || "Anonymous Search"}</h3>
          <p>{search.location || "No location"} · {search.category || "General Business"}</p>
        </div>
        <div className="admin-topbar-meta">
          <button className="btn-ghost admin-back-button" type="button" onClick={onBack}>
            ← Back to Anonymous Searches
          </button>
          {detail?.audit_client && (
            <button className="btn-primary" onClick={() => onOpenAudit?.(detail.audit_client.id)}>
              Open Paid Audit →
            </button>
          )}
        </div>
      </div>

      <div className="admin-grid admin-grid-three">
        <SummaryCard label="Total Score" value={score.total_score ? `${score.total_score}/100` : "—"} />
        <SummaryCard label="PageSpeed" value={pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A"} />
        <SummaryCard label="Upgrade Status" value={linkedAudit ? linkedAudit.audit_status : "Not purchased"} />
      </div>

      <div className="admin-info-list">
        <div><strong>Website:</strong> {search.website_url || business.website || "Not detected"}</div>
        <div><strong>Submitted phone:</strong> {search.manual_contact_phone || search.auto_phone || "Not captured"}</div>
        <div><strong>Detected email:</strong> {search.auto_email || "Not captured"}</div>
        <div><strong>Legacy lead:</strong> {detail?.legacy_lead?.id || "Not linked"}</div>
      </div>

      <SearchAuditSnapshot
        search={search}
        audit={audit}
        title="Full Search Result"
      />

      {error && <div className="admin-inline-message error">{error}</div>}
    </section>
  )
}
