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

export default function LeadDetail({
  token,
  leadId,
  refreshKey,
  onSaved,
  onOpenAudit,
  onUnauthorized,
}) {
  const [detail, setDetail] = useState(null)
  const [form, setForm] = useState({
    status: "new",
    notes: "",
    assigned_to: "",
    follow_up_date: "",
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  useEffect(() => {
    if (!leadId) {
      setDetail(null)
      return
    }

    let cancelled = false

    const fetchLead = async () => {
      setLoading(true)
      setError("")
      setMessage("")
      try {
        const res = await fetch(`${API}/admin/leads/${leadId}`, {
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
          throw new Error(payload.detail || "Could not load lead detail")
        }
        if (!cancelled) {
          setDetail(payload)
          setForm({
            status: payload.lead.status || "new",
            notes: payload.lead.notes || "",
            assigned_to: payload.lead.assigned_to || "",
            follow_up_date: payload.lead.follow_up_date
              ? payload.lead.follow_up_date.slice(0, 10)
              : "",
          })
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load lead detail")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchLead()
    return () => {
      cancelled = true
    }
  }, [token, leadId, refreshKey, onUnauthorized])

  const handleSave = async () => {
    if (!leadId) return
    setSaving(true)
    setError("")
    setMessage("")
    try {
      const res = await fetch(`${API}/admin/leads/${leadId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...form,
          follow_up_date: form.follow_up_date
            ? `${form.follow_up_date}T00:00:00`
            : "",
        }),
      })
      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.()
        return
      }
      const payload = await res.json()
      if (!res.ok) {
        throw new Error(payload.detail || "Could not save lead")
      }
      setMessage("Lead updated successfully.")
      onSaved?.()
    } catch (saveError) {
      setError(saveError.message || "Could not save lead")
    } finally {
      setSaving(false)
    }
  }

  if (!leadId) {
    return <section className="admin-panel-card admin-placeholder">Select a lead to review the full audit snapshot.</section>
  }

  if (loading) {
    return <section className="admin-panel-card admin-placeholder">Loading lead detail...</section>
  }

  if (error && !detail) {
    return <section className="admin-panel-card admin-placeholder admin-error-text">{error}</section>
  }

  const lead = detail?.lead || {}
  const audit = lead.audit_json || {}
  const score = audit.score || {}
  const pagespeed = audit.pagespeed || {}
  const social = audit.social || {}

  return (
    <section className="admin-panel-card admin-panel-card-stretch">
      <div className="admin-section-header">
        <div>
          <h3>{lead.business_name || "Lead Detail"}</h3>
          <p>{lead.location || "No location"} · {lead.category || "General Business"}</p>
        </div>
        {detail?.audit_client && (
          <button className="btn-primary" onClick={() => onOpenAudit?.(detail.audit_client.id)}>
            Open Paid Audit →
          </button>
        )}
      </div>

      <div className="admin-grid admin-grid-three">
        <SummaryCard label="Total Score" value={score.total_score ? `${score.total_score}/100` : "—"} />
        <SummaryCard label="Website Speed" value={pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A"} />
        <SummaryCard label="Social Found" value={social.found_platforms?.length || social.manual_verified?.length || 0} />
      </div>

      <div className="admin-info-list">
        <div><strong>Website:</strong> {lead.website_url || "Not provided"}</div>
        <div><strong>Contact email:</strong> {lead.contact_email || "Not captured"}</div>
        <div><strong>Contact phone:</strong> {lead.contact_phone || "Not captured"}</div>
        <div><strong>Current grade:</strong> {lead.grade || "—"} {lead.score_label ? `· ${lead.score_label}` : ""}</div>
      </div>

      <div className="admin-form-grid">
        <label className="admin-field">
          <span>Status</span>
          <select
            className="admin-select"
            value={form.status}
            onChange={(event) => setForm((value) => ({ ...value, status: event.target.value }))}
          >
            <option value="new">New</option>
            <option value="contacted">Contacted</option>
            <option value="demo_done">Demo done</option>
            <option value="stage4_paid">Stage 4 paid</option>
            <option value="service_signed">Service signed</option>
            <option value="not_interested">Not interested</option>
            <option value="follow_up">Follow up</option>
          </select>
        </label>

        <label className="admin-field">
          <span>Assigned to</span>
          <input
            className="admin-input"
            value={form.assigned_to}
            onChange={(event) => setForm((value) => ({ ...value, assigned_to: event.target.value }))}
            placeholder="Analyst or sales owner"
          />
        </label>

        <label className="admin-field">
          <span>Follow-up date</span>
          <input
            className="admin-input"
            type="date"
            value={form.follow_up_date}
            onChange={(event) => setForm((value) => ({ ...value, follow_up_date: event.target.value }))}
          />
        </label>
      </div>

      <label className="admin-field">
        <span>Internal notes</span>
        <textarea
          className="admin-textarea"
          value={form.notes}
          onChange={(event) => setForm((value) => ({ ...value, notes: event.target.value }))}
          placeholder="Sales conversation notes, objections, next steps, or delivery context"
          rows={7}
        />
      </label>

      {score.top_fixes?.length > 0 && (
        <div className="admin-subsection">
          <h4>Top priority fixes from the free audit</h4>
          <ul className="admin-bullet-list">
            {score.top_fixes.slice(0, 4).map((fix, index) => (
              <li key={`${fix.check}-${index}`}>
                <strong>{fix.check}:</strong> {fix.fix}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(message || error) && (
        <div className={`admin-inline-message ${error ? "error" : "success"}`}>
          {error || message}
        </div>
      )}

      <div className="admin-actions">
        <button className="btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Lead Update"}
        </button>
      </div>
    </section>
  )
}
