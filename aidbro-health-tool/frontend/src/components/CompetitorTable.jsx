import { useState } from "react"

const INTENT_COLOR = {
  local:   "var(--orange)",
  service: "#60a5fa",
  product: "var(--green)",
  brand:   "var(--gray)",
}
const RELEVANCE_OPACITY = { high: 1, medium: 0.75, low: 0.5 }

export default function CompetitorTable({ competitorData, keywordData }) {
  const [tab, setTab] = useState("comparison") // comparison | gaps | keywords

  if (!competitorData) {
    return (
      <div className="comp-empty">
        <span>🏆</span>
        <p>No competitor data available.</p>
      </div>
    )
  }

  const { target, competitors, comparison, gaps, ai_summary, is_mocked } = competitorData
  const dims      = comparison?.dimensions || []
  const allBiz    = [target, ...(competitors || [])]

  return (
    <div className="comp-table">

      {/* Header */}
      <div className="comp-header">
        <div className="comp-header-left">
          <h3>🏆 Competitor Analysis</h3>
          <p>
            {competitors?.length || 0} local competitors analyzed
            {is_mocked && (
              <span className="comp-mock-badge">Demo data</span>
            )}
          </p>
        </div>
        {gaps?.length > 0 && (
          <div className="comp-gaps-pill">
            {gaps.filter(g => g.severity === "critical").length} critical gaps
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="comp-tabs">
        {[
          { key: "comparison", label: "Side-by-Side" },
          { key: "gaps",       label: `Gaps (${gaps?.length || 0})` },
          { key: "keywords",   label: "Keyword Strategy" },
        ].map((t) => (
          <button
            key={t.key}
            className={`comp-tab ${tab === t.key ? "active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Side-by-Side ─────────────────────────────────────────── */}
      {tab === "comparison" && (
        <div className="comp-comparison">

          {/* AI summary */}
          {ai_summary && (
            <div className="comp-ai-summary">
              <span className="comp-ai-icon">🤖</span>
              <p>{ai_summary}</p>
            </div>
          )}

          {/* Comparison table */}
          <div className="comp-matrix">

            {/* Header row */}
            <div className="comp-matrix-header">
              <div className="comp-matrix-dim-label">Dimension</div>
              <div className="comp-matrix-you">YOU</div>
              {competitors?.slice(0, 4).map((c, i) => (
                <div key={i} className="comp-matrix-comp-header">
                  {c.name.split(" ").slice(0, 2).join(" ")}
                </div>
              ))}
            </div>

            {/* Data rows */}
            {dims.map((dim, di) => (
              <div key={di} className="comp-matrix-row">
                <div className="comp-matrix-dim">
                  <span>{dim.icon}</span>
                  {dim.label}
                </div>

                {/* Your value */}
                <div
                  className="comp-matrix-cell comp-matrix-you-cell"
                  style={{
                    color: dim.target_wins ? "var(--green)" : "var(--red)",
                    background: dim.target_wins
                      ? "var(--green-dim)"
                      : "var(--red-dim)",
                  }}
                >
                  {dim.target_value}{dim.unit}
                  {dim.target_wins ? " ↑" : " ↓"}
                </div>

                {/* Competitor values */}
                {competitors?.slice(0, 4).map((comp, ci) => {
                  const val = comp[dim.key]
                  const displayVal =
                    typeof val === "boolean"
                      ? (val ? "✓" : "✗")
                      : val !== undefined && val !== null
                      ? `${val}${dim.unit || ""}`
                      : "—"

                  const compWins =
                    typeof val === "number"
                      ? val > (typeof dim.target_value === "number" ? dim.target_value : 0)
                      : typeof val === "boolean"
                      ? val && !dim.target_wins
                      : false

                  return (
                    <div
                      key={ci}
                      className="comp-matrix-cell"
                      style={{ color: compWins ? "var(--red)" : "var(--gray)" }}
                    >
                      {displayVal}
                    </div>
                  )
                })}
              </div>
            ))}

            {/* Completeness row */}
            <div className="comp-matrix-row comp-matrix-row-last">
              <div className="comp-matrix-dim">
                <span>📊</span>Profile %
              </div>
              <div
                className="comp-matrix-cell comp-matrix-you-cell"
                style={{
                  color: (target?.profile_completeness || 0) >=
                    (comparison?.competitors?.reduce((a, c) => a + (c.profile_completeness || 0), 0) || 0) /
                    Math.max(competitors?.length || 1, 1)
                    ? "var(--green)" : "var(--yellow)",
                }}
              >
                {target?.profile_completeness || 0}%
              </div>
              {competitors?.slice(0, 4).map((comp, ci) => (
                <div key={ci} className="comp-matrix-cell" style={{ color: "var(--gray)" }}>
                  {comp.profile_completeness || 0}%
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Gaps ─────────────────────────────────────────────────── */}
      {tab === "gaps" && (
        <div className="comp-gaps-list">
          {(!gaps || gaps.length === 0) ? (
            <div className="comp-empty">
              <span>✅</span>
              <p>No significant gaps found — you're competitive locally!</p>
            </div>
          ) : (
            gaps.map((gap, i) => (
              <div
                key={i}
                className="comp-gap-item"
                style={{
                  borderLeft: `3px solid ${
                    gap.severity === "critical" ? "var(--red)" : "var(--yellow)"
                  }`,
                  background: gap.severity === "critical"
                    ? "var(--red-dim)" : "var(--yellow-dim)",
                }}
              >
                <div className="comp-gap-top">
                  <span
                    className="comp-gap-dim"
                    style={{
                      color: gap.severity === "critical"
                        ? "var(--red)" : "var(--yellow)",
                    }}
                  >
                    {gap.severity === "critical" ? "🔴" : "🟡"} {gap.dimension}
                  </span>
                  <span className="comp-gap-service">{gap.service}</span>
                </div>
                <p className="comp-gap-message">{gap.message}</p>
                <div className="comp-gap-action">
                  → {gap.action}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── Tab: Keyword Strategy ──────────────────────────────────────── */}
      {tab === "keywords" && (
        <div className="comp-keywords">
          {keywordData?.disclaimer && (
            <div className="kw-disclaimer">{keywordData.disclaimer}</div>
          )}

          {keywordData?.ai_analysis && (
            <div className="comp-ai-summary" style={{ marginBottom: 16 }}>
              <span className="comp-ai-icon">🤖</span>
              <p>{keywordData.ai_analysis}</p>
            </div>
          )}

          <div className="kw-columns">

            {/* Your keywords */}
            <div className="kw-col">
              <div className="kw-col-header" style={{ color: "var(--orange)" }}>
                Your Keyword Strategy
                <span className="kw-col-count">
                  {keywordData?.your_keywords?.length || 0}
                </span>
              </div>
              {(keywordData?.your_keywords || []).map((kw, i) => (
                <div
                  key={i}
                  className="kw-tag"
                  style={{
                    opacity: RELEVANCE_OPACITY[kw.relevance] || 0.8,
                    borderColor: INTENT_COLOR[kw.intent] || "var(--border-dim)",
                  }}
                >
                  <span
                    className="kw-dot"
                    style={{ background: INTENT_COLOR[kw.intent] || "var(--gray)" }}
                  />
                  {kw.keyword}
                </div>
              ))}
              {(!keywordData?.your_keywords?.length) && (
                <p className="kw-empty">Enter a website URL to analyze keywords.</p>
              )}
            </div>

            {/* Missing keywords */}
            <div className="kw-col">
              <div className="kw-col-header" style={{ color: "var(--red)" }}>
                Missing Keywords
                <span className="kw-col-count kw-col-count--missing">
                  {keywordData?.missing_keywords?.length || 0} gaps
                </span>
              </div>
              {(keywordData?.missing_keywords || []).map((kw, i) => (
                <div
                  key={i}
                  className="kw-tag kw-tag--missing"
                >
                  <span className="kw-dot" style={{ background: "var(--red)" }} />
                  {kw.keyword}
                  <span className="kw-missing-label">competitors have this</span>
                </div>
              ))}
              {(!keywordData?.missing_keywords?.length) && (
                <p className="kw-empty">
                  {keywordData?.your_keywords?.length
                    ? "✅ No significant keyword gaps found."
                    : "Add competitor URLs to see gaps."}
                </p>
              )}
            </div>
          </div>

          {/* Intent legend */}
          <div className="kw-legend">
            {Object.entries(INTENT_COLOR).map(([intent, color]) => (
              <div key={intent} className="kw-legend-item">
                <span className="kw-dot" style={{ background: color }} />
                {intent}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
