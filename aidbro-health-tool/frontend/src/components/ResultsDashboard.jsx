import { useState } from "react"
import ScoreRing from "./ScoreRing"

const COLOR = {
  green: "var(--green)",
  yellow: "var(--yellow)",
  red: "var(--red)",
}

function PillarCard({ pillar }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={`pillar-card ${expanded ? "expanded" : ""}`}
      onClick={() => setExpanded((v) => !v)}
    >
      <div className="pillar-header">
        <span className="pillar-icon">{pillar.icon}</span>
        <span className="pillar-name">{pillar.name}</span>
        <span className={`pillar-score-badge ${pillar.color}`}>
          {pillar.score}/{pillar.max}
        </span>
      </div>

      <div className="pillar-bar-track">
        <div
          className={`pillar-bar-fill ${pillar.color}`}
          style={{ width: `${pillar.percent}%` }}
        />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--gray)" }}>
        <span>
          {pillar.checks.filter((c) => c.passed).length}/{pillar.checks.length} checks passed
        </span>
        <span style={{ color: "var(--orange)", fontWeight: 600 }}>
          {expanded ? "▲ Hide" : "▼ Details"}
        </span>
      </div>

      {expanded && (
        <div className="checks-list" onClick={(e) => e.stopPropagation()}>
          {pillar.checks.map((check, i) => (
            <div key={i} className={`check-item ${check.passed ? "pass" : "fail"}`}>
              <span className="check-icon">{check.passed ? "✅" : "❌"}</span>
              <div className="check-content">
                <div className={`check-name ${check.passed ? "pass" : "fail"}`}>
                  {check.check}
                  {check.value ? (
                    <span style={{ color: "var(--gray)", fontWeight: 400, marginLeft: 6 }}>
                      — {check.value}
                    </span>
                  ) : null}
                </div>
                <div className="check-msg">{check.message}</div>
                {!check.passed && check.fix && (
                  <span className="check-fix">💡 {check.fix}</span>
                )}
              </div>
              <span className={`check-pts ${check.passed ? "pass" : "fail"}`}>
                +{check.points_earned}/{check.points_max}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ResultsDashboard({ data, onReset }) {
  const { business, score, pagespeed, social, insights } = data
  const pillars = score?.pillars || {}
  const topFixes = score?.top_fixes || []
  const total = score?.total_score || 0
  const isMocked = business?.is_mocked || false

  const handleDownloadPDF = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/audit/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: business.name.replace(" (Demo Mode)", ""),
          location: business.location,
          website_url: business.website || "",
        }),
      })
      if (!res.ok) throw new Error("PDF generation failed")
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `aidbro_health_${business.name.replace(/\s+/g, "_")}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert("PDF download failed. Make sure the backend is running.")
    }
  }

  const scoreColor =
    total >= 70 ? "var(--green)" :
    total >= 50 ? "var(--yellow)" :
    "var(--red)"

  return (
    <div className="results-page">
      {/* Top bar */}
      <div className="results-topbar">
        <div className="results-topbar-logo">
          Aidbro <span>AI</span>
        </div>
        <div className="results-topbar-actions">
          <button className="pdf-btn" onClick={handleDownloadPDF}>
            📄 Download PDF Report
          </button>
          <button className="btn-ghost" onClick={onReset}>
            ← New Search
          </button>
          <a
            href="https://wa.me/918589999362?text=Hi, I just checked my Digital Health Score and would like to discuss improving it."
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
            style={{ fontSize: 13, padding: "9px 18px" }}
          >
            📞 Talk to Aidbro
          </a>
        </div>
      </div>

      {/* Demo mode notice */}
      {isMocked && (
        <div className="demo-banner">
          ⚠️ <strong>Demo Mode</strong> — Google Places API key not connected.
          Scores shown are illustrative. Add your key in <code>.env</code> to
          get real data.
        </div>
      )}

      <div className="results-content">

        {/* Business header + score ring */}
        <div className="biz-header fade-up">
          <div className="biz-header-left">
            <h2>{business.name}</h2>
            <p>Digital Health Report · Generated by Aidbro AI</p>
            <div className="biz-meta">
              {business.address && (
                <div className="biz-meta-item">
                  📍 <span>{business.address}</span>
                </div>
              )}
              {business.phone && (
                <div className="biz-meta-item">
                  📞 <span>{business.phone}</span>
                </div>
              )}
              {business.website && (
                <div className="biz-meta-item">
                  🌐{" "}
                  <a
                    href={business.website}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: "var(--orange)" }}
                  >
                    {business.website.replace(/^https?:\/\//, "")}
                  </a>
                </div>
              )}
              {business.rating > 0 && (
                <div className="biz-meta-item">
                  ⭐ <span>{business.rating} ({business.total_reviews} reviews)</span>
                </div>
              )}
            </div>
          </div>
          <ScoreRing score={total} size={130} />
        </div>

        {/* Stats row */}
        <div className="stats-row fade-up-d1">
          {[
            {
              value: `${pillars.google_business?.score ?? 0}/30`,
              label: "Google Profile",
              color: COLOR[pillars.google_business?.color],
            },
            {
              value: `${pillars.website?.score ?? 0}/25`,
              label: "Website Quality",
              color: COLOR[pillars.website?.color],
            },
            {
              value: `${pillars.social_media?.score ?? 0}/20`,
              label: "Social Media",
              color: COLOR[pillars.social_media?.color],
            },
            {
              value: `${pillars.reputation?.score ?? 0}/15`,
              label: "Reputation",
              color: COLOR[pillars.reputation?.color],
            },
            {
              value: business.total_reviews || "0",
              label: "Google Reviews",
              color: "var(--white)",
            },
            {
              value: pagespeed?.performance_score
                ? `${pagespeed.performance_score}/100`
                : "N/A",
              label: "Mobile Speed",
              color: pagespeed?.performance_score >= 70
                ? "var(--green)"
                : pagespeed?.performance_score >= 50
                ? "var(--yellow)"
                : "var(--red)",
            },
          ].map((s, i) => (
            <div key={i} className="stat-card">
              <div className="stat-value" style={{ color: s.color }}>
                {s.value}
              </div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* AI Insight card */}
        {insights && (
          <div className="insight-card fade-up-d2">
            <div className="insight-card-header">
              <span>🤖</span>
              <h3>AI-POWERED INSIGHT</h3>
            </div>
            <p className="insight-text">{insights.insight}</p>
            <div className="insight-cta">
              <p>{insights.cta}</p>
              <a
                href="https://wa.me/918589999362?text=Hi, I checked my Digital Health Score and need help improving it."
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{ fontSize: 14 }}
              >
                💬 Book Free Consultation
              </a>
            </div>
          </div>
        )}

        {/* Top priority fixes */}
        {topFixes.length > 0 && (
          <>
            <p className="section-title fade-up">🎯 TOP PRIORITY FIXES</p>
            <div className="fixes-list fade-up">
              {topFixes.map((fix, i) => (
                <div key={i} className="fix-item">
                  <div className="fix-number">{i + 1}</div>
                  <div className="fix-content">
                    <h4>{fix.check}</h4>
                    <p>{fix.fix}</p>
                  </div>
                  <div className="fix-service">{fix.service}</div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Pillar cards */}
        <p className="section-title fade-up-d2">📊 DETAILED PILLAR ANALYSIS</p>
        <div className="pillars-grid fade-up-d2">
          {Object.values(pillars).map((pillar, i) => (
            <PillarCard key={i} pillar={pillar} />
          ))}
        </div>

        {/* PageSpeed details if available */}
        {pagespeed?.found && (
          <>
            <p className="section-title fade-up">🌐 WEBSITE PERFORMANCE DETAILS</p>
            <div className="stats-row fade-up" style={{ marginBottom: 36 }}>
              {[
                { value: `${pagespeed.performance_score}/100`, label: "Performance" },
                { value: `${pagespeed.seo_score}/100`, label: "SEO Score" },
                { value: `${pagespeed.accessibility_score}/100`, label: "Accessibility" },
                { value: pagespeed.lcp || "N/A", label: "Page Load (LCP)" },
                { value: pagespeed.cls || "N/A", label: "Layout Shift (CLS)" },
                { value: pagespeed.is_https ? "Secure ✅" : "Insecure ❌", label: "HTTPS" },
              ].map((s, i) => (
                <div key={i} className="stat-card">
                  <div
                    className="stat-value"
                    style={{
                      fontSize: 18,
                      color:
                        typeof s.value === "string" && s.value.includes("✅")
                          ? "var(--green)"
                          : typeof s.value === "string" && s.value.includes("❌")
                          ? "var(--red)"
                          : "var(--white)",
                    }}
                  >
                    {s.value}
                  </div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Social media details */}
        <p className="section-title fade-up">📱 SOCIAL MEDIA DETECTED</p>
        <div className="stats-row fade-up" style={{ marginBottom: 48 }}>
          {[
            { icon: "📘", label: "Facebook", key: "facebook" },
            { icon: "📸", label: "Instagram", key: "instagram" },
            { icon: "💬", label: "WhatsApp Business", key: "whatsapp_business" },
            { icon: "▶️", label: "YouTube", key: "youtube" },
            { icon: "💼", label: "LinkedIn", key: "linkedin" },
            { icon: "🐦", label: "Twitter / X", key: "twitter" },
          ].map((s, i) => {
            const found = social?.[s.key] || false
            return (
              <div
                key={i}
                className="stat-card"
                style={{
                  borderColor: found
                    ? "rgba(34,197,94,0.3)"
                    : "var(--border-dim)",
                }}
              >
                <div
                  className="stat-value"
                  style={{ fontSize: 24, color: found ? "var(--green)" : "var(--gray-dim)" }}
                >
                  {s.icon}
                </div>
                <div className="stat-label">{s.label}</div>
                <div
                  style={{
                    fontSize: 11,
                    marginTop: 4,
                    color: found ? "var(--green)" : "var(--red)",
                    fontWeight: 600,
                  }}
                >
                  {found ? "✓ Found" : "✗ Not Found"}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer CTA */}
        <div className="results-footer-cta fade-up">
          <div className="results-footer-cta-text">
            <h3>
              Ready to fix your{" "}
              <span style={{ color: "var(--orange)" }}>{total}/100</span> score?
            </h3>
            <p>
              Aidbro's team in Kannur will audit your business personally and
              give you a free action plan — no commitment, no cost.
            </p>
          </div>
          <div className="results-footer-cta-actions">
            <button className="pdf-btn" onClick={handleDownloadPDF}>
              📄 Download PDF
            </button>
            <a
              href="https://wa.me/918589999362?text=Hi! I checked my Digital Health Score — it was {total}/100. Can you help me improve it?"
              target="_blank"
              rel="noreferrer"
              className="btn-primary"
            >
              💬 WhatsApp Aidbro Now
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
