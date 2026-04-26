import { useEffect, useState } from "react"
import ScoreRing from "./ScoreRing"
import ContactCapture from "./ContactCapture"
import SeoReport from "./SeoReport"
import CompetitorTable from "./CompetitorTable"
import SocialImprove from "./SocialImprove"
import PillarChart from "./PillarChart"
import { useAuditPrice } from "./useAuditPrice"
import { useAuth } from "../context/AuthContext"

import { API } from "../config/api"
const C = { green: "var(--green)", yellow: "var(--yellow)", red: "var(--red)" }
const pc = color => C[color] || "var(--gray)"

function CheckRow({ check }) {
  if (check.skipped && check.points_max === 0) return null
  const passed = check.passed

  return (
    <div className={`check-item ${passed ? "pass" : "fail"}`}>
      <span className="check-icon">{passed ? "✅" : "❌"}</span>
      <div className="check-content">
        <div className={`check-name ${passed ? "pass" : "fail"}`}>
          {check.check}
          {check.value && check.value !== "✓" && check.value !== "✗" && (
            <span style={{ color: "var(--gray)", fontWeight: 400, marginLeft: 6 }}>
              — {check.value}
            </span>
          )}
        </div>
        <div className="check-msg">{check.message}</div>
        {!passed && check.fix && <span className="check-fix">💡 {check.fix}</span>}
      </div>
      <span className={`check-pts ${passed ? "pass" : "fail"}`}>
        +{check.points_earned}/{check.points_max}
      </span>
    </div>
  )
}

function PillarCard({ pillar }) {
  const color = pc(pillar.color)
  const pct = pillar.percent || 0

  return (
    <div className="pillar-card-v2">
      <div className="pillar-v2-header">
        <span className="pillar-icon" style={{ fontSize: 24 }}>{pillar.icon}</span>
        <div className="pillar-v2-title">
          <h4>{pillar.name}</h4>
          {pillar.note && <span className="pillar-note">{pillar.note}</span>}
        </div>
        <div className="pillar-v2-score" style={{ color }}>
          <span className="pillar-v2-num">{pillar.score}</span>
          <span className="pillar-v2-max">/{pillar.max}</span>
        </div>
      </div>
      <div className="pillar-v2-bar">
        <div className="pillar-v2-bar-fill" style={{ width: `${pct}%`, background: color }} />
        <span className="pillar-v2-pct" style={{ color }}>{pct}%</span>
      </div>
      <div className="checks-list">
        {pillar.checks.map((c, i) => <CheckRow key={i} check={c} />)}
      </div>
    </div>
  )
}

function PremiumSectionLock({ blurContent, price, isAuthenticated }) {
  return (
    <div className="premium-section-lock">
      <div className="premium-section-lock-blur">{blurContent}</div>
      <div className="premium-section-lock-bar">
        <p>
          🔒 <strong>Full data available in the Detailed Audit Report</strong>
          {" "}— human-verified, AI-synthesized, delivered in 24–48 hours.
        </p>
        <a
          href={isAuthenticated ? "/upgrade" : "/auth"}
          className="btn-primary"
          style={{ fontSize: 13, padding: "9px 18px" }}
        >
          Unlock for {price} →
        </a>
      </div>
    </div>
  )
}

function PremiumFeatures({ price, isAuthenticated }) {
  return (
    <div className="premium-features-section">
      <div className="premium-features-header">
        <div>
          <div className="mid-upgrade-badge">DETAILED AUDIT REPORT</div>
          <h3>Everything in the Full Report</h3>
          <p style={{ color: "var(--gray)", fontSize: 13, marginTop: 6 }}>
            Human-verified data + AI synthesis + 24–48 hour delivery
          </p>
        </div>
        <div className="premium-features-price">
          {price}
          <span>one-time payment · 90 days access</span>
        </div>
      </div>

      <div className="premium-features-grid">
        {[
          { icon: "🏆", title: "5 Competitor Analysis", desc: "Side-by-side rating, reviews, website, photos, profile completeness" },
          { icon: "🔍", title: "Full SEO Crawl", desc: "Every page audited — titles, meta, headings, schema, broken links" },
          { icon: "📱", title: "Social Media Audit", desc: "Manual review of Instagram, Facebook, LinkedIn by our analyst team" },
          { icon: "📊", title: "Keyword Strategy Gaps", desc: "What your competitors rank for that you don't — with fix actions" },
          { icon: "🗺️", title: "Google Maps SEO", desc: "Local pack ranking factors, category optimization, citation analysis" },
          { icon: "✅", title: "Human-Verified Data", desc: "Every automated finding reviewed and corrected by our team" },
          { icon: "🤖", title: "AI Executive Summary", desc: "15–20 page report synthesized from all data sources" },
          { icon: "📞", title: "Follow-up Consultation", desc: "Aidbro team walkthrough of your report and service recommendations" },
        ].map((f, i) => (
          <div key={i} className="premium-feature-item">
            <span className="premium-feature-icon">{f.icon}</span>
            <div className="premium-feature-text">
              <div className="premium-feature-title">{f.title}</div>
              <div className="premium-feature-desc">{f.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ textAlign: "center" }}>
        <a
          href={isAuthenticated ? "/upgrade" : "/auth"}
          className="btn-primary"
          style={{ fontSize: 15, padding: "13px 32px" }}
        >
          {isAuthenticated ? `Get Detailed Audit for ${price} →` : "Register & Get Detailed Audit →"}
        </a>
        <p style={{ fontSize: 11, color: "var(--gray-dim)", marginTop: 8 }}>
          UPI · Cards · Net Banking · 90 days portal access
        </p>
      </div>
    </div>
  )
}

function CompetitorTeaser({ competitorData }) {
  const comps = competitorData?.competitors?.slice(0, 3) || []

  return (
    <div style={{ padding: 16 }}>
      <p style={{ color: "var(--gray)", fontSize: 13, marginBottom: 12 }}>
        {comps.length} local competitors found in your area:
      </p>
      {comps.map((c, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "8px 0",
            borderBottom: "1px solid var(--border-dim)",
            fontSize: 13,
          }}
        >
          <span style={{ color: "var(--white)" }}>{c.name}</span>
          <span style={{ color: c.rating >= 4 ? "var(--green)" : "var(--yellow)" }}>
            {c.rating}★ · {c.review_count} reviews
          </span>
        </div>
      ))}
      <p style={{ fontSize: 12, color: "var(--gray)", marginTop: 12 }}>
        Full comparison table, keyword gaps, and competitive gap analysis locked →
      </p>
    </div>
  )
}

export default function ResultsDashboard({ data, leadId, searchId, onReset }) {
  const { isAuthenticated, authFetch } = useAuth()
  const { price, formatted: priceFormatted } = useAuditPrice()

  const [liveData, setLiveData] = useState(data)
  const [searchPaymentStatus, setSearchPaymentStatus] = useState(null)
  useEffect(() => {
    setLiveData(data)
  }, [data])

  useEffect(() => {
    if (!isAuthenticated || !searchId) {
      setSearchPaymentStatus(null)
      return
    }

    let cancelled = false
    const loadSearchPaymentStatus = async () => {
      try {
        const res = await authFetch(`${API}/payment/status?search_id=${searchId}`)
        const payload = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(payload.detail || "Could not load current search payment status.")
        if (!cancelled) {
          setSearchPaymentStatus(payload)
        }
      } catch {
        if (!cancelled) {
          setSearchPaymentStatus(null)
        }
      }
    }

    loadSearchPaymentStatus()
    return () => {
      cancelled = true
    }
  }, [authFetch, isAuthenticated, searchId])

  const currentData = liveData
  const { business, score, pagespeed, social, seo, competitors, keywords, insights } = currentData
  const pillars = score?.pillars || {}
  const topFixes = score?.top_fixes || []
  const total = score?.total_score || 0
  const isMocked = business?.is_mocked || false
  const hasDetailedAuditForSearch = searchPaymentStatus?.has_paid === true

  const [pdfLoading, setPdfLoading] = useState(false)

  const handleDownloadPDF = async () => {
    setPdfLoading(true)
    try {
      const res = await fetch(`${API}/audit/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: business.name.replace(" (Demo Mode)", ""),
          location: business.location,
          category: business.category || "General Business",
          website_url: business.website || "",
        }),
      })

      if (!res.ok) {
        throw new Error(`Server error ${res.status} — make sure backend is running on port 8000`)
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `aidbro_health_${business.name.replace(/\s+/g, "_")}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert(`PDF Error: ${e.message}`)
    } finally {
      setPdfLoading(false)
    }
  }

  const scoreColor = total >= 70 ? "var(--green)" : total >= 50 ? "var(--yellow)" : "var(--red)"

  return (
    <div className="results-page">
      <div className="results-topbar">
        <div className="results-topbar-logo">Aidbro <span>AI</span></div>
        <div className="results-topbar-actions">
          <button className="pdf-btn" onClick={handleDownloadPDF} disabled={pdfLoading}>
            📄 {pdfLoading ? "Generating..." : "Download PDF"}
          </button>
          <button className="btn-ghost" onClick={onReset}>← New Search</button>
          {!isAuthenticated ? (
            <a href="/auth" className="btn-primary" style={{ fontSize: 13, padding: "9px 16px" }}>
              🔑 Sign In / Register
            </a>
          ) : !hasDetailedAuditForSearch ? (
            <a href="/upgrade" className="btn-primary" style={{ fontSize: 13, padding: "9px 16px" }}>
              ⭐ Unlock {priceFormatted}
            </a>
          ) : (
            <a href="/portal" className="btn-primary" style={{ fontSize: 13, padding: "9px 16px" }}>
              📊 My Portal
            </a>
          )}
          <a
            href="https://wa.me/918589999362?text=Hi, I just checked my Digital Health Score."
            target="_blank"
            rel="noreferrer"
            className="btn-ghost"
            style={{ fontSize: 13 }}
          >
            📞 Talk to Aidbro
          </a>
        </div>
      </div>

      {isMocked && (
        <div className="demo-banner">
          ⚠️ <strong>Demo Mode</strong> — Google API key not connected. Data is illustrative.
        </div>
      )}

      {!hasDetailedAuditForSearch && (
        <div className="upgrade-sticky-banner">
          <span>🔒 Get human-verified competitor rankings, full SEO crawl, social media audit</span>
          <a href={isAuthenticated ? "/upgrade" : "/auth"} className="upgrade-sticky-btn">
            {isAuthenticated ? `Unlock Detailed Audit for ${priceFormatted} →` : "Register Free →"}
          </a>
        </div>
      )}

      <div className="results-content">
        <div className="biz-header fade-up">
          <div className="biz-header-left">
            <h2>{business.name}</h2>
            <p>Digital Health Report · Generated by Aidbro AI</p>
            <div className="biz-meta">
              {business.address && <div className="biz-meta-item">📍 <span>{business.address}</span></div>}
              {business.phone && <div className="biz-meta-item">📞 <span>{business.phone}</span></div>}
              {business.website && (
                <div className="biz-meta-item">
                  🌐{" "}
                  <a href={business.website} target="_blank" rel="noreferrer" style={{ color: "var(--orange)" }}>
                    {business.website.replace(/^https?:\/\//, "")}
                  </a>
                </div>
              )}
              {business.rating > 0 && (
                <div className="biz-meta-item">⭐ <span>{business.rating} ({business.total_reviews} reviews)</span></div>
              )}
              {business.category && <div className="biz-meta-item">🏢 <span>{business.category}</span></div>}
            </div>
          </div>
          <ScoreRing score={total} size={130} />
        </div>

        <div className="stats-and-chart fade-up-d1">
          <div className="stats-row-inline">
            {[
              { value: `${pillars.google_business?.score ?? 0}/${pillars.google_business?.max ?? 30}`, label: "Google Profile", color: pc(pillars.google_business?.color) },
              { value: `${pillars.website?.score ?? 0}/${pillars.website?.max ?? 36}`, label: "Website Quality", color: pc(pillars.website?.color) },
              { value: `${pillars.social_media?.score ?? 0}/${pillars.social_media?.max ?? 20}`, label: "Social Media", color: pc(pillars.social_media?.color) },
              { value: `${pillars.reputation?.score ?? 0}/${pillars.reputation?.max ?? 15}`, label: "Reputation", color: pc(pillars.reputation?.color) },
              { value: business.total_reviews || "0", label: "Google Reviews", color: "var(--white)" },
              {
                value: pagespeed?.performance_score ? `${pagespeed.performance_score}/100` : "N/A",
                label: "Website Speed Score",
                tooltip: "Google's mobile speed score (0–100). Below 50 means customers leave before your page loads.",
                color: pagespeed?.performance_score >= 70 ? "var(--green)"
                  : pagespeed?.performance_score >= 50 ? "var(--yellow)" : "var(--red)",
              },
            ].map((s, i) => (
              <div key={i} className="stat-card" title={s.tooltip || ""}>
                <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
                <div className="stat-label">
                  {s.label}
                  {s.tooltip && <span className="stat-tooltip-icon">ⓘ</span>}
                </div>
              </div>
            ))}
          </div>
          <PillarChart pillars={pillars} />
        </div>

        <div className="demo-banner" style={{ marginBottom: 24 }}>
          <strong>Data consistency note:</strong> identical searches may reuse the latest captured audit snapshot for up to 24 hours so your score stays stable.
          If you have already updated your website, Google profile, or social links, run a fresh check after the cache window or update the official links before rechecking.
        </div>

        {insights && (
          <div className="insight-card fade-up-d2">
            <div className="insight-card-header">
              <span>🤖</span><h3>AI-POWERED INSIGHT</h3>
            </div>
            <div className="insight-bullets">
              {insights.insight
                ? insights.insight.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, 3)
                  .map((s, i) => (
                    <div key={i} className="insight-bullet">
                      <span className="insight-bullet-icon">
                        {i === 0 ? "📊" : i === 1 ? "⚠️" : "🎯"}
                      </span>
                      <span>{s}</span>
                    </div>
                  ))
                : <p className="insight-text">{insights.summary}</p>}
            </div>
            <div className="insight-cta">
              <p>{insights.cta}</p>
              <a
                href="https://wa.me/918589999362?text=Hi! I checked my Digital Health Score and need help."
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

        {!hasDetailedAuditForSearch && (
          <PremiumFeatures price={priceFormatted} isAuthenticated={isAuthenticated} />
        )}

        <p className="section-title fade-up-d2">📊 DETAILED PILLAR ANALYSIS</p>
        <div className="pillars-stack fade-up-d2">
          {Object.values(pillars).map((pillar, i) => (
            <PillarCard key={i} pillar={pillar} />
          ))}
        </div>

        {seo && !seo.error && (
          <>
            <p className="section-title fade-up">🔍 SEO SITE AUDIT</p>
            <SeoReport seoData={seo} />
          </>
        )}

        <p className="section-title fade-up">
          {hasDetailedAuditForSearch ? "🏆 COMPETITOR ANALYSIS" : "🧾 DETAILED AUDIT REPORT"}
        </p>
        {hasDetailedAuditForSearch ? (
          <CompetitorTable competitorData={competitors} keywordData={keywords} />
        ) : (
          <PremiumSectionLock
            price={priceFormatted}
            isAuthenticated={isAuthenticated}
            blurContent={<CompetitorTeaser competitorData={competitors} />}
          />
        )}

        <p className="section-title fade-up">📱 SOCIAL MEDIA PRESENCE</p>
        <div className="social-presence-section fade-up">
          <div className="social-presence-intro">
            <div>
              <h3>Detected profiles and missing link opportunities</h3>
              <p>
                Review what was auto-detected first, then add any missing official links below
                to re-check the audit and refresh the result.
              </p>
            </div>
            <div className="social-presence-note">
              Score points are added from verified Instagram, Facebook, and LinkedIn links.
            </div>
          </div>

          <div className="stats-row social-presence-grid" style={{ marginBottom: 0 }}>
            {[
              { icon: "📘", label: "Facebook", key: "facebook" },
              { icon: "📸", label: "Instagram", key: "instagram" },
              { icon: "💬", label: "WhatsApp Business", key: "whatsapp_business" },
              { icon: "▶️", label: "YouTube", key: "youtube" },
              { icon: "💼", label: "LinkedIn", key: "linkedin" },
              { icon: "🐦", label: "Twitter / X", key: "twitter" },
            ].map((s, i) => {
              const found = social?.[s.key] || false
              const isManual = social?.manual_verified?.includes(s.key)
              const isAuto = social?.auto_detected?.includes(s.key)

              return (
                <div
                  key={i}
                  className="stat-card social-presence-card"
                  style={{ borderColor: found ? "rgba(34,197,94,0.3)" : "var(--border-dim)" }}
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
                  {found && (isManual || isAuto) && (
                    <div style={{ fontSize: 10, color: "var(--gray-dim)", marginTop: 2 }}>
                      {isManual ? "✎ verified" : "◍ auto-detected"}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <SocialImprove
            currentSocial={social}
            businessName={business.name}
            location={business.location}
            category={business.category}
            websiteUrl={business.website}
            onScoreUpdate={(newData) => setLiveData(newData)}
          />
        </div>

        <div style={{ marginBottom: 36 }} />

        {pagespeed?.found && (
          <>
            <p className="section-title fade-up">🌐 WEBSITE PERFORMANCE</p>
            <div className="stats-row fade-up" style={{ marginBottom: 36 }}>
              {[
                {
                  value: `${pagespeed.performance_score}/100`,
                  label: "Speed Score",
                  tooltip: "Google's mobile speed score. Below 50 = customers leave before page loads.",
                  color: pagespeed.performance_score >= 70 ? "var(--green)"
                    : pagespeed.performance_score >= 50 ? "var(--yellow)" : "var(--red)",
                },
                { value: `${pagespeed.seo_score}/100`, label: "SEO Score", color: "var(--white)" },
                { value: `${pagespeed.accessibility_score}/100`, label: "Accessibility", color: "var(--white)" },
                { value: pagespeed.lcp || "N/A", label: "Page Load (LCP)", color: "var(--white)" },
                { value: pagespeed.cls || "N/A", label: "Layout Shift", color: "var(--white)" },
                {
                  value: pagespeed.is_https ? "✅ Secure" : "❌ Insecure",
                  label: "HTTPS",
                  color: pagespeed.is_https ? "var(--green)" : "var(--red)",
                },
              ].map((s, i) => (
                <div key={i} className="stat-card" title={s.tooltip || ""}>
                  <div className="stat-value" style={{ fontSize: 18, color: s.color }}>{s.value}</div>
                  <div className="stat-label">
                    {s.label}
                    {s.tooltip && <span className="stat-tooltip-icon">ⓘ</span>}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="results-footer-cta fade-up">
          {hasDetailedAuditForSearch ? (
            <>
              <div className="results-footer-cta-text">
                <h3>Your <span style={{ color: scoreColor }}>{total}/100</span> score is ready to fix.</h3>
                <p>Check your portal for the full detailed report.</p>
              </div>
              <div className="results-footer-cta-actions">
                <button className="pdf-btn" onClick={handleDownloadPDF}>📄 Download PDF</button>
                <a href="/portal" className="btn-primary">📊 View My Portal</a>
              </div>
            </>
          ) : (
            <>
              <div className="results-footer-cta-text">
                <h3>Ready for a full detailed analysis?</h3>
                <p>
                  Detailed Audit ({priceFormatted} one-time) — human-verified competitor
                  rankings, keyword analysis, social media audit, 15–20 page AI report,
                  delivered in 24–48 hours.
                </p>
                <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
                  {["✅ Human-verified", "🏆 5 competitors", "🔍 Full SEO crawl", "📱 Social audit", "📄 15–20 page report"]
                    .map((f, i) => <span key={i} style={{ fontSize: 12, color: "var(--gray)" }}>{f}</span>)}
                </div>
              </div>
              <div className="results-footer-cta-actions">
                <button className="pdf-btn" onClick={handleDownloadPDF}>📄 Free PDF</button>
                <a href={isAuthenticated ? "/upgrade" : "/auth"} className="btn-primary">
                  {isAuthenticated ? "⭐ Get Detailed Audit →" : "🔑 Register & Unlock →"}
                </a>
              </div>
            </>
          )}
        </div>
      </div>

      <ContactCapture leadId={leadId} businessName={business?.name} score={total} />
    </div>
  )
}
