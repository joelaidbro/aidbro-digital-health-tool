import { useEffect, useState } from "react"
import { useAuth } from "../context/AuthContext"
import SeoReport from "../components/SeoReport"
import PillarChart from "../components/PillarChart"

import { API } from "../config/api"

const STEP_ICON = {
  complete: "OK",
  active: "...",
  pending: "--",
}

const STEP_COLOR = {
  complete: "var(--green)",
  active: "var(--orange)",
  pending: "var(--gray-dim)",
}

const ACTIVE_AUDIT_STATES = new Set(["pending", "in_progress", "review", "completed"])

function formatDate(value) {
  if (!value) return "-"
  try {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  } catch {
    return "-"
  }
}

function prettyStatus(value) {
  if (!value) return "Not started"
  return value.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase())
}

function SnapshotCheckRow({ check }) {
  if (check?.skipped && check.points_max === 0) return null
  const passed = !!check?.passed

  return (
    <div className={`check-item ${passed ? "pass" : "fail"}`}>
      <span className="check-icon">{passed ? "OK" : "NO"}</span>
      <div className="check-content">
        <div className={`check-name ${passed ? "pass" : "fail"}`}>
          {check?.check}
          {check?.value && (
            <span style={{ color: "var(--gray)", fontWeight: 400, marginLeft: 6 }}>
              - {check.value}
            </span>
          )}
        </div>
        <div className="check-msg">{check?.message}</div>
        {!passed && check?.fix && (
          <span className="check-fix">{check.fix}</span>
        )}
      </div>
      <span className={`check-pts ${passed ? "pass" : "fail"}`}>
        +{check?.points_earned ?? 0}/{check?.points_max ?? 0}
      </span>
    </div>
  )
}

function SnapshotPillarCard({ pillar }) {
  return (
    <div className="pillar-card-v2">
      <div className="pillar-v2-header">
        <span className="pillar-icon" style={{ fontSize: 24 }}>{pillar.icon}</span>
        <div className="pillar-v2-title">
          <h4>{pillar.name}</h4>
          {pillar.note && <span className="pillar-note">{pillar.note}</span>}
        </div>
        <div className="pillar-v2-score" style={{ color: "var(--white)" }}>
          <span className="pillar-v2-num">{pillar.score}</span>
          <span className="pillar-v2-max">/{pillar.max}</span>
        </div>
      </div>
      <div className="pillar-v2-bar">
        <div className="pillar-v2-bar-fill" style={{ width: `${pillar.percent || 0}%` }} />
        <span className="pillar-v2-pct">{pillar.percent || 0}%</span>
      </div>
      <div className="checks-list">
        {(pillar.checks || []).map((check, index) => (
          <SnapshotCheckRow key={`${pillar.name}-${index}`} check={check} />
        ))}
      </div>
    </div>
  )
}

function SearchHistoryCard({
  search,
  loading,
  onViewSnapshot,
  onUpgrade,
  onOpenAudit,
}) {
  const linkedJob = search.linked_audit_job

  return (
    <div className="pillar-card">
      <div className="pillar-header" style={{ alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div className="pillar-name" style={{ marginBottom: 6 }}>
            {search.business_name}
          </div>
          <div className="check-msg">
            {search.location}
            {search.category ? ` | ${search.category}` : ""}
          </div>
        </div>
        <div
          style={{
            minWidth: 78,
            textAlign: "right",
            color: "var(--white)",
            fontWeight: 800,
            fontSize: 22,
          }}
        >
          {search.total_score ?? "-"}
          <div style={{ color: "var(--gray)", fontSize: 12, fontWeight: 600 }}>
            Grade {search.grade || "-"}
          </div>
        </div>
      </div>

      <div className="checks-list">
        <div className="check-item pass">
          <div className="check-content">
            <div className="check-name pass">Saved On</div>
            <div className="check-msg">{formatDate(search.created_at)}</div>
          </div>
        </div>
        <div className="check-item pass">
          <div className="check-content">
            <div className="check-name pass">Website</div>
            <div className="check-msg">{search.website_url || "Not detected"}</div>
          </div>
        </div>
        <div className="check-item pass">
          <div className="check-content">
            <div className="check-name pass">Contact Discovered</div>
            <div className="check-msg">
              {search.auto_phone || search.auto_email
                ? [search.auto_phone, search.auto_email].filter(Boolean).join(" | ")
                : "No auto-captured contact yet"}
            </div>
          </div>
        </div>
        <div className="check-item pass">
          <div className="check-content">
            <div className="check-name pass">Detailed Audit</div>
            <div className="check-msg">
              {linkedJob
                ? prettyStatus(linkedJob.audit_status)
                : "Not purchased for this search"}
            </div>
          </div>
        </div>
      </div>

      <div
        className="results-footer-cta-actions"
        style={{ marginTop: 18 }}
      >
        <button className="btn-secondary" onClick={() => onViewSnapshot(search.id)}>
          {loading ? "Loading..." : "View Saved Result"}
        </button>
        {linkedJob ? (
          <button className="btn-primary" onClick={() => onOpenAudit(search)}>
            Open Audit Status
          </button>
        ) : (
          <button className="btn-primary" onClick={() => onUpgrade(search)}>
            Start Detailed Audit
          </button>
        )}
      </div>
    </div>
  )
}

function SearchSnapshot({ snapshot, onUpgrade, onOpenAudit, onDownloadPdf, pdfLoading, hasLinkedAudit }) {
  const audit = snapshot?.audit || {}
  const score = audit.score || {}
  const business = audit.business || {}
  const pagespeed = audit.pagespeed || {}
  const social = audit.social || {}
  const seo = audit.seo || {}
  const competitors = audit.competitors || {}
  const keywords = audit.keywords || {}
  const insights = audit.insights || {}
  const pillars = Object.values(score.pillars || {})
  const topFixes = score.top_fixes || []

  return (
    <div className="portal-report-tab fade-up">
      <p className="section-title">Saved Search Snapshot</p>

      <div className="stats-row" style={{ marginTop: 0, marginBottom: 24 }}>
        {[
          { label: "Business", value: business.name || snapshot.search?.business_name || "-" },
          { label: "Saved On", value: formatDate(snapshot.search?.created_at) },
          { label: "Total Score", value: score.total_score ? `${score.total_score}/100` : "-" },
          { label: "Grade", value: score.grade ? `${score.grade} - ${score.label || ""}` : "-" },
          { label: "Google Rating", value: business.rating ? `${business.rating} (${business.total_reviews || 0})` : "-" },
          { label: "Website Speed", value: pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A" },
        ].map((item) => (
          <div key={item.label} className="stat-card">
            <div className="stat-label">{item.label}</div>
            <div style={{ fontSize: 14, color: "var(--white)", fontWeight: 700, marginTop: 8 }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>

      <div className="demo-banner" style={{ marginBottom: 24, borderRadius: 12 }}>
        This saved result keeps score consistency by reusing the latest captured snapshot for identical searches within 24 hours.
        If your business details changed after this audit, run a fresh check after the cache window for updated live data.
      </div>

      {(business.website || business.phone || business.email) && (
        <>
          <p className="section-title">Business Details</p>
          <div className="insight-card" style={{ marginBottom: 24 }}>
            <p className="insight-text" style={{ marginBottom: 10 }}>
              {business.address || "Address not captured for this search."}
            </p>
            <p className="insight-text" style={{ marginBottom: 6 }}>
              Website: {business.website || "Not detected"}
            </p>
            <p className="insight-text" style={{ marginBottom: 6 }}>
              Phone: {business.phone || "Not detected"}
            </p>
            <p className="insight-text">
              Email: {business.email || "Not detected"}
            </p>
          </div>
        </>
      )}

      {audit.insights?.summary && (
        <>
          <p className="section-title">AI Summary</p>
          <div className="insight-card" style={{ marginBottom: 24 }}>
            <p className="insight-text">{audit.insights.summary}</p>
            {audit.insights.insight && (
              <p className="insight-text" style={{ marginTop: 12 }}>
                {audit.insights.insight}
              </p>
            )}
          </div>
        </>
      )}

      {!!pillars.length && (
        <>
          <p className="section-title">Score Breakdown</p>
          <div className="stats-and-chart" style={{ marginBottom: 24 }}>
            <div className="stats-row-inline">
              {pillars.map((pillar) => (
                <div key={pillar.name} className="stat-card">
                  <div className="stat-value" style={{ color: "var(--white)", fontSize: 20 }}>
                    {pillar.score}/{pillar.max}
                  </div>
                  <div className="stat-label">{pillar.name}</div>
                </div>
              ))}
            </div>
            <PillarChart pillars={score.pillars || {}} />
          </div>

          <p className="section-title">Detailed Pillar Analysis</p>
          <div className="pillars-stack" style={{ marginBottom: 24 }}>
            {pillars.map((pillar) => (
              <SnapshotPillarCard key={pillar.name} pillar={pillar} />
            ))}
          </div>
        </>
      )}

      {!!topFixes.length && (
        <>
          <p className="section-title">Priority Fixes</p>
          <div className="pillars-grid" style={{ marginBottom: 24 }}>
            {topFixes.map((item, index) => (
              <div key={`${item.check}-${index}`} className="pillar-card">
                <div className="pillar-header">
                  <span className="pillar-name">{item.check}</span>
                </div>
                <div className="check-msg" style={{ marginBottom: 12 }}>
                  Impact score: {item.impact}
                </div>
                <p className="insight-text">{item.fix || "No fix recorded."}</p>
                {item.service && (
                  <div className="check-msg" style={{ marginTop: 12 }}>
                    Suggested service: {item.service}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {!!social && (
        <>
          <p className="section-title">Social Presence</p>
          <div className="stats-row social-presence-grid" style={{ marginBottom: 24 }}>
            {[
              { label: "Facebook", key: "facebook" },
              { label: "Instagram", key: "instagram" },
              { label: "WhatsApp Business", key: "whatsapp_business" },
              { label: "YouTube", key: "youtube" },
              { label: "LinkedIn", key: "linkedin" },
              { label: "Twitter / X", key: "twitter" },
            ].map((item) => (
              <div key={item.key} className="stat-card social-presence-card">
                <div
                  className="stat-value"
                  style={{
                    fontSize: 18,
                    color: social[item.key] ? "var(--green)" : "var(--red)",
                  }}
                >
                  {social[item.key] ? "Found" : "Missing"}
                </div>
                <div className="stat-label">{item.label}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {seo && !seo.error && (
        <>
          <p className="section-title">SEO Site Audit</p>
          <SeoReport seoData={seo} />
        </>
      )}

      {competitors?.competitors?.length > 0 && (
        <>
          <p className="section-title">Competitor Analysis</p>
          <div className="pillars-grid" style={{ marginBottom: 24 }}>
            {(competitors.competitors || []).slice(0, 4).map((competitor, index) => (
              <div key={`${competitor.name}-${index}`} className="pillar-card">
                <div className="pillar-header">
                  <span className="pillar-name">{competitor.name}</span>
                </div>
                <div className="check-msg" style={{ marginBottom: 8 }}>
                  {competitor.address || "Address not captured"}
                </div>
                <div className="checks-list">
                  <div className="check-item pass">
                    <div className="check-content">
                      <div className="check-name pass">Rating</div>
                      <div className="check-msg">{competitor.rating || 0} stars</div>
                    </div>
                  </div>
                  <div className="check-item pass">
                    <div className="check-content">
                      <div className="check-name pass">Reviews</div>
                      <div className="check-msg">{competitor.review_count || 0} reviews</div>
                    </div>
                  </div>
                  <div className="check-item pass">
                    <div className="check-content">
                      <div className="check-name pass">Website</div>
                      <div className="check-msg">{competitor.website_url || "Not listed"}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {!!competitors.gaps?.length && (
            <>
              <p className="section-title">Competitive Gaps</p>
              <div className="fixes-list" style={{ marginBottom: 24 }}>
                {competitors.gaps.slice(0, 5).map((gap, index) => (
                  <div key={`${gap.dimension}-${index}`} className="fix-item">
                    <div className="fix-number">{index + 1}</div>
                    <div className="fix-content">
                      <h4>{gap.dimension}</h4>
                      <p>{gap.message}</p>
                    </div>
                    <div className="fix-service">{gap.service || gap.severity}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!!keywords?.missing_keywords?.length && (
            <>
              <p className="section-title">Missing Keywords</p>
              <div className="pillars-grid" style={{ marginBottom: 24 }}>
                {keywords.missing_keywords.slice(0, 12).map((keyword, index) => (
                  <div key={`${keyword.keyword}-${index}`} className="pillar-card">
                    <div className="pillar-header">
                      <span className="pillar-name">{keyword.keyword}</span>
                    </div>
                    <div className="check-msg">
                      Competitors target this term and your business is currently missing it.
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {pagespeed?.found && (
        <>
          <p className="section-title">Website Performance</p>
          <div className="stats-row" style={{ marginBottom: 24 }}>
            {[
              { label: "Speed Score", value: pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A" },
              { label: "SEO Score", value: pagespeed.seo_score ? `${pagespeed.seo_score}/100` : "N/A" },
              { label: "Accessibility", value: pagespeed.accessibility_score ? `${pagespeed.accessibility_score}/100` : "N/A" },
              { label: "LCP", value: pagespeed.lcp || "N/A" },
              { label: "CLS", value: pagespeed.cls || "N/A" },
              { label: "HTTPS", value: pagespeed.is_https ? "Secure" : "Insecure" },
            ].map((item) => (
              <div key={item.label} className="stat-card">
                <div className="stat-value" style={{ fontSize: 18 }}>{item.value}</div>
                <div className="stat-label">{item.label}</div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="results-footer-cta">
        <div className="results-footer-cta-text">
          <h3>{hasLinkedAudit ? "Your saved result is ready to review" : "Need a full manual report for this search?"}</h3>
          <p>
            {hasLinkedAudit
              ? "Download the free audit PDF here, or switch to Audit Status / My Report for your paid workflow."
              : "Select this saved audit and continue to the paid detailed audit flow."}
          </p>
        </div>
        <div className="results-footer-cta-actions">
          <button className="pdf-btn" onClick={() => onDownloadPdf(snapshot)} disabled={pdfLoading}>
            {pdfLoading ? "Generating PDF..." : "Download PDF"}
          </button>
          {hasLinkedAudit ? (
            <button className="btn-primary" onClick={() => onOpenAudit(snapshot.search)}>
              Open Audit Status
            </button>
          ) : (
            <button className="btn-primary" onClick={() => onUpgrade(snapshot.search)}>
              Upgrade This Search
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ClientPortal({ onLogout }) {
  const { user, authFetch, logout } = useAuth()
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState({ searches: [], audit_jobs: [] })
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState("history")
  const [report, setReport] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [snapshotPdfLoading, setSnapshotPdfLoading] = useState(false)
  const [error, setError] = useState("")
  const [snapshot, setSnapshot] = useState(null)
  const [snapshotLoadingId, setSnapshotLoadingId] = useState(null)
  const [selectedAuditSearchId, setSelectedAuditSearchId] = useState(() => {
    const raw = sessionStorage.getItem("aidbro_active_search_id")
    return raw ? Number(raw) : null
  })

  const latestSearch = history.searches[0] || null

  const fetchHistory = async () => {
    const res = await authFetch(`${API}/portal/history`)
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || "Could not load your saved searches.")
    }
    const data = await res.json()
    setHistory({
      searches: data.searches || [],
      audit_jobs: data.audit_jobs || [],
    })
    return data
  }

  const fetchStatus = async (searchId = selectedAuditSearchId) => {
    if (!searchId) {
      setStatus(null)
      return null
    }
    const suffix = searchId ? `?search_id=${searchId}` : ""
    const res = await authFetch(`${API}/portal/status${suffix}`)
    if (res.status === 403 || res.status === 404) {
      setStatus(null)
      return null
    }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || "Could not load audit status.")
    }
    const data = await res.json()
    setStatus(data)
    return data
  }

  const loadPortal = async () => {
    setLoading(true)
    setError("")
    try {
      const historyData = await fetchHistory()
      const activeSearchId = Number(sessionStorage.getItem("aidbro_active_search_id") || "0")
      const paidSearches = (historyData?.searches || []).filter((search) => search.linked_audit_job)
      const activeSearch = paidSearches.find((search) => search.id === activeSearchId)
      const fallbackSearch = paidSearches.length === 1 ? paidSearches[0] : null
      const resolvedSearch = activeSearch || fallbackSearch

      let statusData = null
      if (resolvedSearch) {
        setSelectedAuditSearchId(resolvedSearch.id)
        statusData = await fetchStatus(resolvedSearch.id)
      } else {
        setSelectedAuditSearchId(null)
        setStatus(null)
      }

      if (resolvedSearch) {
        setTab("status")
      } else if (statusData?.report_ready) {
        setTab("status")
      } else {
        setTab("history")
      }
    } catch (err) {
      setError(err.message || "Could not load your portal.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPortal()
  }, [])

  useEffect(() => {
    if (!status || !ACTIVE_AUDIT_STATES.has(status.audit_status)) return undefined
    const intervalId = setInterval(() => {
      fetchStatus(selectedAuditSearchId).catch(() => {})
    }, 60000)
    return () => clearInterval(intervalId)
  }, [selectedAuditSearchId, status])

  const fetchReport = async (searchId = selectedAuditSearchId) => {
    setReportLoading(true)
    setError("")
    try {
      const suffix = searchId ? `?search_id=${searchId}` : ""
      const res = await authFetch(`${API}/portal/report${suffix}`)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Report not ready.")
      }
      setReport(await res.json())
      setTab("report")
    } catch (err) {
      setError(err.message || "Could not load report.")
    } finally {
      setReportLoading(false)
    }
  }

  const fetchSnapshot = async (searchId) => {
    setSnapshotLoadingId(searchId)
    setError("")
    try {
      const res = await authFetch(`${API}/portal/searches/${searchId}`)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Could not load saved result.")
      }
      const payload = await res.json()
      setSnapshot(payload)
      if (payload.search?.linked_audit_job) {
        sessionStorage.setItem("aidbro_active_search_id", String(payload.search.id))
        setSelectedAuditSearchId(payload.search.id)
        await fetchStatus(payload.search.id)
      }
      setTab("snapshot")
    } catch (err) {
      setError(err.message || "Could not load saved result.")
    } finally {
      setSnapshotLoadingId(null)
    }
  }

  const handleDownloadPDF = async (searchId = selectedAuditSearchId) => {
    try {
      const suffix = searchId ? `?search_id=${searchId}` : ""
      const res = await authFetch(`${API}/portal/report/pdf${suffix}`)
      if (!res.ok) {
        setError("PDF not available yet.")
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = "aidbro_detailed_report.pdf"
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      setError("PDF download failed.")
    }
  }

  const handleDownloadSnapshotPDF = async (savedSnapshot) => {
    if (!savedSnapshot?.audit?.business && !savedSnapshot?.search) return

    const business = savedSnapshot.audit?.business || {}
    const businessName = (business.name || savedSnapshot.search?.business_name || "").replace(" (Demo Mode)", "")
    const location = business.location || savedSnapshot.search?.location || ""
    const category = business.category || savedSnapshot.search?.category || "General Business"
    const websiteUrl = business.website || savedSnapshot.search?.website_url || ""

    setSnapshotPdfLoading(true)
    setError("")
    try {
      const res = await fetch(`${API}/audit/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName,
          location,
          category,
          website_url: websiteUrl,
        }),
      })

      if (!res.ok) {
        throw new Error("Could not generate saved-result PDF.")
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `aidbro_saved_result_${businessName.replace(/\s+/g, "_") || "audit"}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message || "Saved-result PDF failed.")
    } finally {
      setSnapshotPdfLoading(false)
    }
  }

  const handleNewSearch = () => {
    sessionStorage.removeItem("aidbro_active_search_id")
    window.location.href = "/"
  }

  const handleUpgrade = (search) => {
    if (!search?.id) return
    sessionStorage.setItem("aidbro_active_search_id", String(search.id))
    setSelectedAuditSearchId(search.id)
    window.location.href = "/upgrade"
  }

  const handleOpenAudit = async (search) => {
    if (!search?.id) return
    sessionStorage.setItem("aidbro_active_search_id", String(search.id))
    setSelectedAuditSearchId(search.id)
    setReport(null)
    try {
      const statusData = await fetchStatus(search.id)
      if (statusData?.report_ready) {
        setTab("status")
      } else {
        setTab("status")
      }
    } catch (err) {
      setError(err.message || "Could not load audit status.")
    }
  }

  if (loading) {
    return (
      <div className="portal-page">
        <div className="loading-orb" style={{ margin: "80px auto" }} />
      </div>
    )
  }

  return (
    <div className="portal-page">
      <div className="portal-topbar">
        <div className="portal-topbar-logo">
          Aidbro <span>AI</span>
          <span className="navbar-badge">Client Portal</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, color: "var(--gray)" }}>
            {user?.name || user?.email}
          </span>
          <button
            className="btn-ghost"
            onClick={() => {
              logout()
              onLogout?.()
            }}
          >
            Sign Out
          </button>
        </div>
      </div>

      <div className="portal-content">
        <div className="portal-welcome fade-up">
          <div>
            <h2>
              Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}!
            </h2>
            <p style={{ color: "var(--gray)", fontSize: 14, marginTop: 4 }}>
              {status?.status_label
                || (history.searches.some((search) => search.linked_audit_job)
                  ? "Select a paid search from history to track that audit and open its final report."
                  : null)
                || (history.searches.length
                  ? `You have ${history.searches.length} saved search${history.searches.length > 1 ? "es" : ""} in your account.`
                  : "Run your first search and we will save it here automatically.")}
            </p>
          </div>

          <div className="results-footer-cta-actions">
            <button className="btn-secondary" onClick={handleNewSearch}>
              Start New Search
            </button>
            {latestSearch && !latestSearch.linked_audit_job && (
              <button className="btn-primary" onClick={() => handleUpgrade(latestSearch)}>
                Unlock Detailed Audit
              </button>
            )}
            {status?.report_ready && (
              <>
                <button
                  className="btn-primary"
                  onClick={fetchReport}
                  disabled={reportLoading}
                >
                  {reportLoading ? "Loading..." : "View Report"}
                </button>
                <button className="pdf-btn" onClick={handleDownloadPDF}>
                  Download PDF
                </button>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="demo-banner" style={{ marginBottom: 20, borderRadius: 8 }}>
            {error}
            <button
              style={{
                marginLeft: 12,
                color: "var(--orange)",
                background: "none",
                border: "none",
                cursor: "pointer",
                fontSize: 12,
              }}
              onClick={() => setError("")}
            >
              Dismiss
            </button>
          </div>
        )}

        <div
          className="portal-tabs"
          style={{
            marginBottom: 0,
            background: "var(--navy-light)",
            borderRadius: "8px 8px 0 0",
            border: "1px solid var(--border-dim)",
            borderBottom: "none",
          }}
        >
          <button
            className={`portal-tab ${tab === "history" ? "active" : ""}`}
            onClick={() => setTab("history")}
          >
            My Searches
          </button>
          {status && (
            <button
              className={`portal-tab ${tab === "status" ? "active" : ""}`}
              onClick={() => setTab("status")}
            >
              Audit Status
            </button>
          )}
          {snapshot && (
            <button
              className={`portal-tab ${tab === "snapshot" ? "active" : ""}`}
              onClick={() => setTab("snapshot")}
            >
              Saved Result
            </button>
          )}
          {status?.report_ready && (
            <button
              className={`portal-tab ${tab === "report" ? "active" : ""}`}
              onClick={() => {
                if (!report) fetchReport()
                else setTab("report")
              }}
            >
              My Report
            </button>
          )}
        </div>

        {tab === "history" && (
          <div className="portal-status-tab">
            {!history.searches.length ? (
              <div className="insight-card" style={{ marginTop: 24 }}>
                <div className="insight-card-header">
                  <h3>NO SAVED SEARCHES YET</h3>
                </div>
                <p className="insight-text">
                  Once you run a free audit while logged in, it will appear here with its score,
                  detected contact details, and an option to convert that exact search into a
                  detailed paid audit later.
                </p>
                <div className="insight-cta">
                  <p>Start with a free audit and build your history from there.</p>
                  <button className="btn-primary" onClick={handleNewSearch}>
                    Run Free Audit
                  </button>
                </div>
              </div>
            ) : (
              <>
                <p className="section-title" style={{ marginTop: 24 }}>
                  Saved Searches
                </p>
                <div className="pillars-grid">
                  {history.searches.map((search) => (
                    <SearchHistoryCard
                      key={search.id}
                      search={search}
                      loading={snapshotLoadingId === search.id}
                      onViewSnapshot={fetchSnapshot}
                      onUpgrade={handleUpgrade}
                      onOpenAudit={handleOpenAudit}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {tab === "status" && status && (
          <div className="portal-status-tab">
            {status.search_name && (
              <p className="section-title" style={{ marginTop: 24 }}>
                Tracking: {status.search_name}
              </p>
            )}
            <div className="portal-steps">
              {(status.steps || []).map((step, index, allSteps) => (
                <div key={step.step || index} className="portal-step">
                  <div
                    className="portal-step-icon"
                    style={{ color: STEP_COLOR[step.state] }}
                  >
                    {STEP_ICON[step.state]}
                  </div>
                  <div className="portal-step-body">
                    <div
                      className="portal-step-label"
                      style={{ color: STEP_COLOR[step.state] }}
                    >
                      {step.label}
                    </div>
                  </div>
                  {index < allSteps.length - 1 && (
                    <div
                      className="portal-step-connector"
                      style={{
                        background: step.state === "complete"
                          ? "var(--green)"
                          : "var(--border-dim)",
                      }}
                    />
                  )}
                </div>
              ))}
            </div>

            <div className="stats-row" style={{ marginTop: 24 }}>
              {[
                {
                  label: "Access Until",
                  value: formatDate(status.access_until),
                },
                {
                  label: "Current Stage",
                  value: prettyStatus(status.audit_status),
                },
                {
                  label: "Typical Delivery",
                  value: "24 - 48 hours",
                },
                {
                  label: "Support",
                  value: "WhatsApp Us",
                  link: "https://wa.me/918589999362",
                },
              ].map((item) => (
                <div key={item.label} className="stat-card">
                  <div className="stat-label">{item.label}</div>
                  {item.link ? (
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: "var(--orange)", fontSize: 12, fontWeight: 600 }}
                    >
                      {item.value}
                    </a>
                  ) : (
                    <div style={{ fontSize: 12, color: "var(--white)", fontWeight: 600 }}>
                      {item.value}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {!status.report_ready && (
              <div className="insight-card" style={{ marginTop: 24 }}>
                <div className="insight-card-header">
                  <h3>YOUR REPORT IS BEING PREPARED</h3>
                </div>
                <p className="insight-text">
                  Our team is collecting and manually verifying your business data.
                  This typically takes 24 to 48 hours. When the report is approved,
                  it will appear here for download.
                </p>
                <div className="insight-cta">
                  <p>Need an update on delivery?</p>
                  <a
                    href="https://wa.me/918589999362?text=Hi, I would like an update on my detailed audit."
                    target="_blank"
                    rel="noreferrer"
                    className="btn-primary"
                    style={{ fontSize: 13 }}
                  >
                    Contact Aidbro
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "snapshot" && snapshot && (
          <SearchSnapshot
            snapshot={snapshot}
            onUpgrade={handleUpgrade}
            onOpenAudit={handleOpenAudit}
            onDownloadPdf={handleDownloadSnapshotPDF}
            pdfLoading={snapshotPdfLoading}
            hasLinkedAudit={!!snapshot.search?.linked_audit_job}
          />
        )}

        {tab === "report" && report && (
          <div className="portal-report-tab fade-up">
            {status?.search_name && (
              <p className="section-title" style={{ marginTop: 20 }}>
                Report For: {status.search_name}
              </p>
            )}
            {report.ai_synthesis?.summary && (
              <>
                <p className="section-title" style={{ marginTop: 20 }}>
                  AI Executive Summary
                </p>
                <div className="insight-card" style={{ marginBottom: 24 }}>
                  <p className="insight-text">{report.ai_synthesis.summary}</p>
                </div>
              </>
            )}

            {(report.social_report?.instagram || report.social_report?.facebook || report.social_report?.linkedin) && (
              <>
                <p className="section-title">Social Media Analysis</p>
                <div className="pillars-grid" style={{ marginBottom: 24 }}>
                  {["instagram", "facebook", "linkedin"].map((platform) => {
                    const data = report.social_report?.[platform]
                    if (!data) return null
                    return (
                      <div key={platform} className="pillar-card">
                        <div className="pillar-header">
                          <span className="pillar-name" style={{ textTransform: "capitalize" }}>
                            {platform}
                          </span>
                        </div>
                        <div className="checks-list">
                          {Object.entries(data).map(([key, value]) => (
                            key !== "analyst_notes" ? (
                              <div key={key} className="check-item pass">
                                <div className="check-content">
                                  <div className="check-name pass" style={{ textTransform: "capitalize" }}>
                                    {key.replace(/_/g, " ")}
                                  </div>
                                  <div className="check-msg">{String(value)}</div>
                                </div>
                              </div>
                            ) : null
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}

            {report.analyst_notes && (
              <>
                <p className="section-title">Analyst Notes</p>
                <div className="insight-card" style={{ marginBottom: 24 }}>
                  <p className="insight-text">{report.analyst_notes}</p>
                </div>
              </>
            )}

            <div className="results-footer-cta">
              <div className="results-footer-cta-text">
                <h3>Your full report is ready</h3>
                <p>Download the complete PDF or discuss the recommendations with our team.</p>
              </div>
              <div className="results-footer-cta-actions">
                <button className="pdf-btn" onClick={handleDownloadPDF}>
                  Download PDF
                </button>
                <a
                  href="https://wa.me/918589999362?text=Hi, I have reviewed my report and would like to discuss the recommendations."
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary"
                >
                  Discuss with Aidbro
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
