import { useEffect, useState } from "react"

import { API } from "../../src/config/api"

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
  const pagespeed = audit.pagespeed || {}
  const business = audit.business || {}
  const linkedAudit = detail?.linked_audit_job
  const topFixes = score.top_fixes || []

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>{search.business_name || "Anonymous Search"}</h3>
          <p>{search.location || "No location"} · {search.category || "General Business"}</p>
        </div>
        {detail?.audit_client && (
          <button className="btn-primary" onClick={() => onOpenAudit?.(detail.audit_client.id)}>
            Open Paid Audit →
          </button>
        )}
      </div>

      <div className="admin-grid admin-grid-three">
        <SummaryCard label="Total Score" value={score.total_score ? `${score.total_score}/100` : "—"} />
        <SummaryCard label="PageSpeed" value={pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A"} />
        <SummaryCard label="Upgrade Status" value={linkedAudit ? linkedAudit.audit_status : "Not purchased"} />
      </div>

      <div className="admin-info-list">
        <div><strong>Website:</strong> {search.website_url || business.website || "Not detected"}</div>
        <div><strong>Auto phone:</strong> {search.auto_phone || business.phone || "Not captured"}</div>
        <div><strong>Auto email:</strong> {search.auto_email || business.email || "Not captured"}</div>
        <div><strong>Legacy lead:</strong> {detail?.legacy_lead?.id || "Not linked"}</div>
      </div>

      {topFixes.length > 0 && (
        <div className="admin-subsection">
          <h4>Top priority fixes</h4>
          <ul className="admin-bullet-list">
            {topFixes.slice(0, 5).map((fix, index) => (
              <li key={`${fix.check}-${index}`}>
                <strong>{fix.check}:</strong> {fix.fix}
              </li>
            ))}
          </ul>
        </div>
      )}

      {score.pillars && (
        <div className="admin-subsection">
          <h4>Pillar summary</h4>
          <div className="admin-grid admin-grid-two">
            {Object.values(score.pillars).map((pillar) => (
              <div key={pillar.name} className="admin-summary-card">
                <div className="admin-summary-label">{pillar.name}</div>
                <div className="admin-summary-value">{pillar.score}/{pillar.max}</div>
                <div className="admin-metric-hint">{pillar.percent}% complete</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && <div className="admin-inline-message error">{error}</div>}
    </section>
  )
}
