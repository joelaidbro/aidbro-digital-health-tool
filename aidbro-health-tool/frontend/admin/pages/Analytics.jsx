import { useEffect, useState } from "react"

import { API } from "../../src/config/api"

function MetricCard({ label, value, hint }) {
  return (
    <div className="admin-metric-card">
      <div className="admin-metric-label">{label}</div>
      <div className="admin-metric-value">{value}</div>
      {hint && <div className="admin-metric-hint">{hint}</div>}
    </div>
  )
}

function BarChart({ title, rows, valueKey = "count", labelKey = "label", color = "var(--orange)" }) {
  const max = Math.max(...rows.map((row) => row[valueKey] || 0), 1)

  return (
    <div className="admin-chart-card">
      <div className="admin-section-header">
        <h3>{title}</h3>
      </div>
      <div className="admin-bar-chart">
        {rows.map((row) => (
          <div key={row[labelKey]} className="admin-bar-row">
            <div className="admin-bar-label">{row[labelKey]}</div>
            <div className="admin-bar-track">
              <div
                className="admin-bar-fill"
                style={{
                  width: `${((row[valueKey] || 0) / max) * 100}%`,
                  background: color,
                }}
              />
            </div>
            <div className="admin-bar-value">{row[valueKey] || 0}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Analytics({ token, refreshKey, onUnauthorized }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const loadDashboard = async () => {
      setLoading(true)
      setError("")
      try {
        const res = await fetch(`${API}/admin/dashboard`, {
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
          throw new Error(payload.detail || "Could not load dashboard")
        }
        if (!cancelled) {
          setData(payload)
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError.message || "Could not load dashboard")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadDashboard()
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, onUnauthorized])

  if (loading) {
    return <div className="admin-panel-card">Loading dashboard data...</div>
  }

  if (error) {
    return <div className="admin-panel-card admin-error-text">{error}</div>
  }

  const metrics = data?.metrics || {}

  return (
    <div className="admin-dashboard">
      <div className="admin-grid admin-grid-metrics">
        <MetricCard label="Total Searches" value={metrics.searches_total || 0} hint="All saved audit runs" />
        <MetricCard label="Anonymous Searches" value={metrics.anonymous_searches || 0} hint="No account attached" />
        <MetricCard label="Registered Users" value={metrics.registered_users || 0} hint="Accounts created" />
        <MetricCard label="Legacy Leads" value={metrics.leads_total || 0} hint="Older CRM records" />
        <MetricCard label="Paid Clients" value={metrics.paid_clients || 0} hint="Stage 4 purchases" />
        <MetricCard label="Conversion Rate" value={`${metrics.conversion_rate || 0}%`} hint="Search to paid" />
        <MetricCard label="Audits Today" value={metrics.audits_today || 0} hint="Paid audits today" />
        <MetricCard label="Revenue This Month" value={`Rs ${(metrics.revenue_month || 0).toLocaleString("en-IN")}`} hint="Captured payments" />
        <MetricCard label="High Usage Alerts" value={metrics.high_activity_alerts || 0} hint={`IPs/accounts over ${data?.alert_threshold || 0} searches in ${data?.alert_window_hours || 24}h`} />
      </div>

      <div className="admin-grid admin-grid-two">
        <BarChart title="Search Sources" rows={data?.search_sources || []} labelKey="label" valueKey="count" color="var(--orange-lt)" />
        <BarChart title="Lead Funnel" rows={data?.funnel || []} labelKey="status" valueKey="count" color="var(--orange)" />
      </div>

      <div className="admin-grid admin-grid-two">
        <BarChart title="Audit Pipeline" rows={data?.audit_pipeline || []} labelKey="status" valueKey="count" color="var(--green)" />
        <BarChart title="Score Distribution" rows={data?.score_distribution || []} labelKey="label" valueKey="count" color="var(--orange-lt)" />
      </div>

      <div className="admin-grid admin-grid-two">
        <BarChart title="Average Score by Category" rows={data?.score_by_category || []} labelKey="category" valueKey="avg_score" color="var(--yellow)" />
      </div>

      <div className="admin-grid admin-grid-two">
        <BarChart title="High Activity by IP" rows={data?.ip_alerts || []} labelKey="label" valueKey="count" color="var(--red)" />
        <BarChart title="High Activity by Account" rows={data?.account_alerts || []} labelKey="label" valueKey="count" color="var(--red)" />
      </div>
    </div>
  )
}
