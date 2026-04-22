import { useState } from "react"

const SEVERITY_COLOR = {
  critical: "var(--red)",
  warning:  "var(--yellow)",
  info:     "var(--gray)",
}
const SEVERITY_BG = {
  critical: "var(--red-dim)",
  warning:  "var(--yellow-dim)",
  info:     "rgba(255,255,255,0.04)",
}
const SEVERITY_ICON = {
  critical: "🔴",
  warning:  "🟡",
  info:     "🔵",
}
const IMPACT_COLOR = {
  High:   "var(--red)",
  Medium: "var(--yellow)",
  Low:    "var(--green)",
}

export default function SeoReport({ seoData }) {
  const [tab, setTab] = useState("overview")  // overview | issues | recommendations

  if (!seoData || seoData.error) {
    return (
      <div className="seo-empty">
        <span>🔍</span>
        <p>
          {seoData?.error
            ? `SEO scan unavailable: ${seoData.error}`
            : "Enter a website URL to get an SEO audit."}
        </p>
      </div>
    )
  }

  const summary  = seoData.summary || {}
  const issues   = seoData.issues || []
  const recs     = seoData.recommendations || []
  const site     = seoData.site_level || {}
  const pages    = seoData.pages || []
  const hp       = pages[0] || {}

  const criticals = issues.filter((i) => i.severity === "critical").length
  const warnings  = issues.filter((i) => i.severity === "warning").length

  return (
    <div className="seo-report">

      {/* Header */}
      <div className="seo-report-header">
        <div className="seo-report-meta">
          <h3>🔍 SEO Site Audit</h3>
          <p>
            {summary.pages_crawled || 1} page(s) crawled ·{" "}
            <span style={{ color: criticals > 0 ? "var(--red)" : "var(--green)" }}>
              {criticals} critical
            </span>{" "}
            ·{" "}
            <span style={{ color: warnings > 0 ? "var(--yellow)" : "var(--green)" }}>
              {warnings} warnings
            </span>
          </p>
        </div>
        {/* Score pill */}
        <div
          className="seo-score-pill"
          style={{
            background: seoData.score >= 8
              ? "var(--green-dim)"
              : seoData.score >= 4
              ? "var(--yellow-dim)"
              : "var(--red-dim)",
            color: seoData.score >= 8
              ? "var(--green)"
              : seoData.score >= 4
              ? "var(--yellow)"
              : "var(--red)",
          }}
        >
          SEO Score +{seoData.score || 0} pts
        </div>
      </div>

      {/* Tabs */}
      <div className="seo-tabs">
        {[
          { key: "overview",        label: "Overview" },
          { key: "issues",          label: `Issues (${issues.length})` },
          { key: "recommendations", label: "AI Recommendations" },
        ].map((t) => (
          <button
            key={t.key}
            className={`seo-tab ${tab === t.key ? "active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Overview ───────────────────────────────────────────────── */}
      {tab === "overview" && (
        <div className="seo-overview">

          {/* Quick stats grid */}
          <div className="seo-stats-grid">
            {[
              {
                icon: "🤖", label: "robots.txt",
                val: site.has_robots_txt ? "✓ Found" : "✗ Missing",
                ok: site.has_robots_txt,
              },
              {
                icon: "🗺️", label: "sitemap.xml",
                val: site.has_sitemap ? "✓ Found" : "✗ Missing",
                ok: site.has_sitemap,
              },
              {
                icon: "🔒", label: "HTTPS",
                val: site.all_pages_https ? "✓ Secure" : "✗ Insecure",
                ok: site.all_pages_https,
              },
              {
                icon: "📝", label: "Schema Markup",
                val: summary.has_schema
                  ? `✓ ${(summary.schema_types || []).join(", ") || "Found"}`
                  : "✗ Missing",
                ok: summary.has_schema,
              },
              {
                icon: "📢", label: "Open Graph",
                val: summary.og_complete ? "✓ Complete" : "✗ Incomplete",
                ok: summary.og_complete,
              },
              {
                icon: "📄", label: "Word Count",
                val: `${summary.homepage_word_count || 0} words`,
                ok: (summary.homepage_word_count || 0) >= 300,
              },
              {
                icon: "🖼️", label: "Images Alt Text",
                val: summary.images_missing_alt === 0
                  ? "✓ All OK"
                  : `✗ ${summary.images_missing_alt} missing`,
                ok: summary.images_missing_alt === 0,
              },
              {
                icon: "⚡", label: "Load Time",
                val: hp.load_time_ms ? `${hp.load_time_ms}ms` : "N/A",
                ok: (hp.load_time_ms || 9999) < 3000,
              },
            ].map((s, i) => (
              <div key={i} className="seo-stat">
                <span className="seo-stat-icon">{s.icon}</span>
                <div className="seo-stat-body">
                  <div className="seo-stat-label">{s.label}</div>
                  <div
                    className="seo-stat-value"
                    style={{ color: s.ok ? "var(--green)" : "var(--red)" }}
                  >
                    {s.val}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Homepage title preview */}
          {summary.homepage_title && (
            <div className="seo-preview-block">
              <p className="seo-preview-label">GOOGLE SEARCH PREVIEW</p>
              <div className="seo-preview-card">
                <div className="seo-preview-url">
                  {seoData.url?.replace(/^https?:\/\//, "")}
                </div>
                <div className="seo-preview-title">{summary.homepage_title}</div>
                {hp.meta_description && (
                  <div className="seo-preview-desc">
                    {hp.meta_description.slice(0, 160)}
                    {hp.meta_description.length > 160 ? "..." : ""}
                  </div>
                )}
              </div>
              <div className="seo-preview-hints">
                <span style={{ color: hp.title_ok ? "var(--green)" : "var(--yellow)" }}>
                  Title: {hp.title_length || 0} chars {hp.title_ok ? "✓" : "(ideal: 30–65)"}
                </span>
                <span style={{ color: hp.meta_desc_ok ? "var(--green)" : "var(--yellow)" }}>
                  Meta: {hp.meta_desc_length || 0} chars {hp.meta_desc_ok ? "✓" : "(ideal: 120–165)"}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Issues ─────────────────────────────────────────────────── */}
      {tab === "issues" && (
        <div className="seo-issues-list">
          {issues.length === 0 ? (
            <div className="seo-empty">
              <span>✅</span>
              <p>No issues found — great SEO health!</p>
            </div>
          ) : (
            issues.map((issue, i) => (
              <div
                key={i}
                className="seo-issue-item"
                style={{ background: SEVERITY_BG[issue.severity] }}
              >
                <span className="seo-issue-icon">
                  {SEVERITY_ICON[issue.severity]}
                </span>
                <div className="seo-issue-body">
                  <div
                    className="seo-issue-title"
                    style={{ color: SEVERITY_COLOR[issue.severity] }}
                  >
                    {issue.issue}
                  </div>
                  <div className="seo-issue-fix">💡 Fix: {issue.fix}</div>
                  {issue.url && issue.url !== seoData.url && (
                    <div className="seo-issue-url">
                      Page: {issue.url.replace(/^https?:\/\//, "")}
                    </div>
                  )}
                </div>
                <span
                  className="seo-issue-badge"
                  style={{
                    background: SEVERITY_BG[issue.severity],
                    color: SEVERITY_COLOR[issue.severity],
                    border: `1px solid ${SEVERITY_COLOR[issue.severity]}`,
                  }}
                >
                  {issue.severity}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── Tab: AI Recommendations ─────────────────────────────────────── */}
      {tab === "recommendations" && (
        <div className="seo-recs-list">
          {recs.length === 0 ? (
            <div className="seo-empty">
              <span>🤖</span>
              <p>Recommendations loading...</p>
            </div>
          ) : (
            recs.map((rec, i) => (
              <div key={i} className="seo-rec-item">
                <div className="seo-rec-number">{rec.priority}</div>
                <div className="seo-rec-body">
                  <div className="seo-rec-title">{rec.title}</div>
                  <div className="seo-rec-problem">{rec.problem}</div>
                  <div className="seo-rec-fix">
                    <span>→</span> {rec.fix}
                  </div>
                </div>
                <div className="seo-rec-meta">
                  <span
                    className="seo-rec-impact"
                    style={{
                      color: IMPACT_COLOR[rec.impact] || "var(--gray)",
                      borderColor: IMPACT_COLOR[rec.impact] || "var(--gray)",
                    }}
                  >
                    {rec.impact} Impact
                  </span>
                  <span className="seo-rec-service">{rec.service}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
