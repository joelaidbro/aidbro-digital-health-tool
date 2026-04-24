import { useEffect, useState } from "react"

import { API } from "../../src/config/api"
const BLANK_SOCIAL = {
  profile_url: "",
  followers: "",
  posting_frequency: "",
  profile_quality: "",
  engagement_notes: "",
  improvement_actions: "",
}

function flattenSection(value, prefix = "") {
  if (value === null || value === undefined) {
    return []
  }

  if (typeof value !== "object" || Array.isArray(value)) {
    return [{ path: prefix || "value", value }]
  }

  const rows = []
  Object.entries(value).forEach(([key, nested]) => {
    const nextPath = prefix ? `${prefix}.${key}` : key
    if (nested && typeof nested === "object" && !Array.isArray(nested)) {
      rows.push(...flattenSection(nested, nextPath))
    } else {
      rows.push({ path: nextPath, value: nested })
    }
  })
  return rows
}

function readValue(value) {
  if (value === null || value === undefined || value === "") return "—"
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

function buildOverrideDrafts(detailedAudit) {
  const maps = [
    ["basic_audit", detailedAudit?.basic_audit_overrides || {}],
    ["seo", detailedAudit?.seo_overrides || {}],
    ["competitors", detailedAudit?.competitors_overrides || {}],
    ["keywords", detailedAudit?.keywords_overrides || {}],
    ["local_seo", detailedAudit?.local_seo_overrides || {}],
  ]
  const drafts = {}
  maps.forEach(([section, values]) => {
    Object.entries(values).forEach(([fieldName, entry]) => {
      drafts[`${section}:${fieldName}`] = {
        section,
        field_name: fieldName,
        original_value: entry.original_value,
        override_value: entry.override_value ?? "",
        reason: entry.reason ?? "",
      }
    })
  })
  return drafts
}

export default function AuditEditor({
  token,
  auditId,
  user,
  refreshKey,
  onSaved,
  onUnauthorized,
}) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [approving, setApproving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [activeTab, setActiveTab] = useState("automated")
  const [status, setStatus] = useState("pending")
  const [notes, setNotes] = useState("")
  const [aiSummary, setAiSummary] = useState("")
  const [aiNextSteps, setAiNextSteps] = useState("")
  const [instagram, setInstagram] = useState(BLANK_SOCIAL)
  const [facebook, setFacebook] = useState(BLANK_SOCIAL)
  const [linkedin, setLinkedin] = useState(BLANK_SOCIAL)
  const [overrideDrafts, setOverrideDrafts] = useState({})

  useEffect(() => {
    if (!auditId) {
      setDetail(null)
      return
    }

    let cancelled = false

    const fetchAudit = async () => {
      setLoading(true)
      setError("")
      setMessage("")
      try {
        const res = await fetch(`${API}/admin/audits/${auditId}`, {
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
          throw new Error(payload.detail || "Could not load audit detail")
        }
        if (!cancelled) {
          const detailedAudit = payload.detailed_audit || {}
          setDetail(payload)
          setStatus(payload.client?.audit_status || "pending")
          setNotes(detailedAudit.analyst_notes || "")
          setAiSummary(detailedAudit.ai_synthesis_json?.summary || "")
          setAiNextSteps(detailedAudit.ai_synthesis_json?.next_steps || "")
          setInstagram({ ...BLANK_SOCIAL, ...(detailedAudit.instagram_manual || {}) })
          setFacebook({ ...BLANK_SOCIAL, ...(detailedAudit.facebook_manual || {}) })
          setLinkedin({ ...BLANK_SOCIAL, ...(detailedAudit.linkedin_manual || {}) })
          setOverrideDrafts(buildOverrideDrafts(detailedAudit))
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load audit detail")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchAudit()
    return () => {
      cancelled = true
    }
  }, [token, auditId, refreshKey, onUnauthorized])

  if (!auditId) {
    return <section className="admin-panel-card admin-placeholder">Select a paid client to start editing the detailed audit workspace.</section>
  }

  if (loading) {
    return <section className="admin-panel-card admin-placeholder">Loading audit workspace...</section>
  }

  if (error && !detail) {
    return <section className="admin-panel-card admin-placeholder admin-error-text">{error}</section>
  }

  const detailedAudit = detail?.detailed_audit || {}
  const sections = [
    { key: "basic_audit", label: "Basic Audit Snapshot", data: detailedAudit.basic_audit_json },
    { key: "seo", label: "SEO Crawl", data: detailedAudit.seo_crawler_json },
    { key: "competitors", label: "Competitors", data: detailedAudit.competitors_json },
    { key: "keywords", label: "Keywords", data: detailedAudit.keywords_json },
    { key: "local_seo", label: "Local SEO", data: detailedAudit.local_seo_json },
  ]

  const handleOverrideChange = (sectionKey, fieldName, field, value, originalValue) => {
    const key = `${sectionKey}:${fieldName}`
    setOverrideDrafts((current) => ({
      ...current,
      [key]: {
        section: sectionKey,
        field_name: fieldName,
        original_value: current[key]?.original_value ?? originalValue,
        override_value: field === "override_value" ? value : current[key]?.override_value ?? "",
        reason: field === "reason" ? value : current[key]?.reason ?? "",
      },
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    setError("")
    setMessage("")
    try {
      const overrides = Object.values(overrideDrafts).filter(
        (entry) => String(entry.override_value || "").trim() || String(entry.reason || "").trim()
      )

      const res = await fetch(`${API}/admin/audits/${auditId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          audit_status: status,
          analyst_notes: notes,
          ai_synthesis_json: {
            summary: aiSummary,
            next_steps: aiNextSteps,
          },
          instagram_manual: instagram,
          facebook_manual: facebook,
          linkedin_manual: linkedin,
          overrides,
        }),
      })
      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.()
        return
      }
      const payload = await res.json()
      if (!res.ok) {
        throw new Error(payload.detail || "Could not save audit workspace")
      }
      setDetail((current) => ({
        ...current,
        client: payload.client,
        detailed_audit: payload.detailed_audit,
      }))
      setMessage("Audit workspace saved.")
      onSaved?.()
    } catch (saveError) {
      setError(saveError.message || "Could not save audit workspace")
    } finally {
      setSaving(false)
    }
  }

  const handleApprove = async () => {
    setApproving(true)
    setError("")
    setMessage("")
    try {
      const res = await fetch(`${API}/admin/audits/${auditId}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ report_pdf_path: detailedAudit.report_pdf_path || "" }),
      })
      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.()
        return
      }
      const payload = await res.json()
      if (!res.ok) {
        throw new Error(payload.detail || "Could not approve audit")
      }
      setDetail((current) => ({
        ...current,
        client: payload.client,
        detailed_audit: payload.detailed_audit,
      }))
      setStatus(payload.client.audit_status)
      setMessage("Report approved successfully.")
      onSaved?.()
    } catch (approveError) {
      setError(approveError.message || "Could not approve audit")
    } finally {
      setApproving(false)
    }
  }

  const client = detail?.client || {}
  const lead = detail?.lead || {}

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header admin-section-header-tight">
        <div>
          <h3>{lead.business_name || client.email || "Detailed Audit"}</h3>
          <p>{client.email} · Paid {client.paid_at ? new Date(client.paid_at).toLocaleDateString("en-IN") : "—"}</p>
        </div>
        <div className="admin-topbar-meta">
          <select className="admin-select" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="pending">Pending</option>
            <option value="in_progress">In progress</option>
            <option value="review">Review</option>
            <option value="completed">Completed</option>
            <option value="delivered">Delivered</option>
          </select>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Workspace"}
          </button>
        </div>
      </div>

      <div className="admin-tabs">
        {[
          { key: "automated", label: "Automated Data" },
          { key: "social", label: "Social Media" },
          { key: "notes", label: "Notes & AI" },
          ...(user.role === "manager" || user.role === "super_admin" || user.role === "admin"
            ? [{ key: "approve", label: "Approve" }]
            : []),
        ].map((tab) => (
          <button
            key={tab.key}
            className={`admin-tab ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "automated" && (
        <div className="admin-automated-sections">
          {sections.map((section) => {
            const rows = flattenSection(section.data || {})
            return (
              <div key={section.key} className="admin-subsection">
                <h4>{section.label}</h4>
                {!rows.length && <p className="admin-muted">No automated data available yet.</p>}
                {rows.length > 0 && (
                  <div className="admin-override-grid">
                    {rows.map((row) => {
                      const draft = overrideDrafts[`${section.key}:${row.path}`] || {}
                      return (
                        <div key={`${section.key}:${row.path}`} className="admin-override-row">
                          <div>
                            <div className="admin-override-path">{row.path}</div>
                            <div className="admin-override-original">{readValue(row.value)}</div>
                          </div>
                          <input
                            className="admin-input"
                            placeholder="Override value"
                            value={draft.override_value ?? ""}
                            onChange={(event) =>
                              handleOverrideChange(
                                section.key,
                                row.path,
                                "override_value",
                                event.target.value,
                                row.value
                              )
                            }
                          />
                          <input
                            className="admin-input"
                            placeholder="Reason for override"
                            value={draft.reason ?? ""}
                            onChange={(event) =>
                              handleOverrideChange(
                                section.key,
                                row.path,
                                "reason",
                                event.target.value,
                                row.value
                              )
                            }
                          />
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {activeTab === "social" && (
        <div className="admin-grid admin-grid-three">
          {[
            ["Instagram", instagram, setInstagram],
            ["Facebook", facebook, setFacebook],
            ["LinkedIn", linkedin, setLinkedin],
          ].map(([label, values, setter]) => (
            <div key={label} className="admin-subsection admin-social-editor">
              <h4>{label}</h4>
              {Object.keys(BLANK_SOCIAL).map((field) => (
                <label key={field} className="admin-field">
                  <span>{field.replace(/_/g, " ")}</span>
                  {field.includes("notes") || field.includes("actions") ? (
                    <textarea
                      className="admin-textarea"
                      rows={3}
                      value={values[field] || ""}
                      onChange={(event) => setter((current) => ({ ...current, [field]: event.target.value }))}
                    />
                  ) : (
                    <input
                      className="admin-input"
                      value={values[field] || ""}
                      onChange={(event) => setter((current) => ({ ...current, [field]: event.target.value }))}
                    />
                  )}
                </label>
              ))}
            </div>
          ))}
        </div>
      )}

      {activeTab === "notes" && (
        <div className="admin-grid admin-grid-two">
          <label className="admin-field">
            <span>Analyst notes</span>
            <textarea
              className="admin-textarea"
              rows={12}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Manual observations, delivery notes, and internal commentary"
            />
          </label>
          <div className="admin-stack">
            <label className="admin-field">
              <span>AI executive summary</span>
              <textarea
                className="admin-textarea"
                rows={8}
                value={aiSummary}
                onChange={(event) => setAiSummary(event.target.value)}
                placeholder="High-level business summary for the final report"
              />
            </label>
            <label className="admin-field">
              <span>Recommended next steps</span>
              <textarea
                className="admin-textarea"
                rows={5}
                value={aiNextSteps}
                onChange={(event) => setAiNextSteps(event.target.value)}
                placeholder="Concrete actions the client should take next"
              />
            </label>
          </div>
        </div>
      )}

      {activeTab === "approve" && (
        <div className="admin-approval-card">
          <div className="admin-grid admin-grid-three">
            <div className="admin-summary-card">
              <div className="admin-summary-label">Workspace status</div>
              <div className="admin-summary-value">{status}</div>
            </div>
            <div className="admin-summary-card">
              <div className="admin-summary-label">Overrides saved</div>
              <div className="admin-summary-value">{Object.keys(overrideDrafts).length}</div>
            </div>
            <div className="admin-summary-card">
              <div className="admin-summary-label">Report approval</div>
              <div className="admin-summary-value">
                {detailedAudit.report_approved ? "Approved" : "Awaiting approval"}
              </div>
            </div>
          </div>

          <div className="admin-subsection">
            <h4>Approval readiness</h4>
            <ul className="admin-bullet-list">
              <li>Analyst notes: {notes.trim() ? "ready" : "missing"}</li>
              <li>AI summary: {aiSummary.trim() ? "ready" : "missing"}</li>
              <li>Manual social review: {(instagram.profile_url || facebook.profile_url || linkedin.profile_url) ? "started" : "not started"}</li>
            </ul>
          </div>

          <button className="btn-primary" onClick={handleApprove} disabled={approving}>
            {approving ? "Approving..." : "Approve & Notify Client →"}
          </button>
        </div>
      )}

      {(message || error) && (
        <div className={`admin-inline-message ${error ? "error" : "success"}`}>
          {error || message}
        </div>
      )}
    </section>
  )
}
