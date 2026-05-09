import { useMemo } from "react"

function SummaryCard({ label, value }) {
  return (
    <div className="admin-summary-card">
      <div className="admin-summary-label">{label}</div>
      <div className="admin-summary-value">{value || "-"}</div>
    </div>
  )
}

function DetailSection({ title, children }) {
  return (
    <section className="admin-subsection admin-audit-section">
      <h4>{title}</h4>
      {children}
    </section>
  )
}

function DataNote() {
  return <div className="admin-data-note">Data not available</div>
}

function StatusMark({ passed }) {
  return (
    <span className={`admin-check-status ${passed ? "is-pass" : "is-fail"}`}>
      {passed ? "✓" : "✕"}
    </span>
  )
}

function formatValue(value, fallback = "Not available") {
  if (value === null || value === undefined || value === "") return fallback
  if (typeof value === "boolean") return value ? "Yes" : "No"
  return String(value)
}

function scoreTone(score) {
  if (score < 40) return "danger"
  if (score <= 70) return "warning"
  return "success"
}

function scorePercent(value, max = 100) {
  if (!max) return 0
  return Math.max(0, Math.min(100, Math.round((Number(value || 0) / Number(max)) * 100)))
}

function SectionFieldGrid({ fields }) {
  return (
    <div className="admin-grid admin-grid-three">
      {fields.map((field) => (
        <div key={field.label} className="admin-summary-card admin-audit-field">
          <div className="admin-summary-label">{field.label}</div>
          <div className="admin-audit-field-value">{formatValue(field.value)}</div>
        </div>
      ))}
    </div>
  )
}

export default function AuditJsonSections({ audit }) {
  const hasAuditData = useMemo(() => Boolean(audit && Object.keys(audit).length), [audit])

  if (!hasAuditData) {
    return <div className="admin-inline-message error">No audit data available for this search</div>
  }

  const score = audit?.score || {}
  const business = audit?.business || {}
  const pagespeed = audit?.pagespeed || {}
  const scoreValue = Number(score.total_score || 0)
  const scoreToneClass = scoreTone(scoreValue)
  const pillars = Object.values(score.pillars || {})
  const social = audit?.social || {}
  const seo = audit?.seo || {}
  const competitors = audit?.competitors || {}
  const keywords = audit?.keywords || {}
  const topFixes = [...(score.top_fixes || [])].sort((a, b) => (b.impact || 0) - (a.impact || 0))

  return (
    <div className="admin-stack">
      <DetailSection title="Section 1 - Business Info">
        {Object.keys(business).length ? (
          <>
            <SectionFieldGrid
              fields={[
                { label: "Name", value: business.name },
                { label: "Location", value: business.location },
                { label: "Category", value: business.category },
                { label: "Address", value: business.address },
                { label: "Phone", value: business.phone },
                { label: "Email", value: business.email },
                { label: "Website", value: business.website },
                { label: "Google Rating", value: business.rating },
                { label: "Total Reviews", value: business.total_reviews },
                { label: "Google Profile Found", value: business.google_profile_found },
                { label: "Google Match Confidence", value: business.google_match_confidence },
              ]}
            />
            {business.google_profile_found === false && (
              <div className="admin-inline-message warning">
                No Google profile was found for this search.
              </div>
            )}
          </>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 2 - Overall Score">
        {Object.keys(score).length ? (
          <>
            <div className="admin-grid admin-grid-three">
              <SummaryCard label="Total Score" value={`${scoreValue}/100`} />
              <SummaryCard label="Grade" value={score.grade || "-"} />
              <SummaryCard label="Label" value={score.label || "-"} />
            </div>
            <div className="admin-score-bar">
              <div className="admin-score-bar-track">
                <div
                  className={`admin-score-bar-fill ${scoreToneClass}`}
                  style={{ width: `${scorePercent(scoreValue)}%` }}
                />
              </div>
              <div className="admin-table-sub">{scorePercent(scoreValue)}%</div>
            </div>
          </>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 3 - Pillar Scores">
        {pillars.length ? (
          <div className="admin-stack-list">
            {pillars.map((pillar, index) => {
              const visibleChecks = (pillar.checks || []).filter(
                (check) => !(check.passed === true && !check.fix),
              )

              return (
                <div key={`${pillar.name}-${index}`} className="admin-panel-card admin-audit-block">
                  <div className="admin-section-header admin-section-header-tight">
                    <div>
                      <h4>{pillar.icon} {pillar.name}</h4>
                      <div className="admin-muted">
                        {pillar.score}/{pillar.max} - {pillar.percent}%
                      </div>
                    </div>
                  </div>

                  {!visibleChecks.length ? (
                    <DataNote />
                  ) : (
                    <div className="admin-stack-list">
                      {visibleChecks.map((check, checkIndex) => (
                        <div key={`${check.check}-${checkIndex}`} className="admin-audit-check">
                          <div className="admin-audit-check-head">
                            <div className="admin-audit-check-title">
                              <StatusMark passed={Boolean(check.passed)} />
                              <span>{check.check}</span>
                            </div>
                            <div className="admin-table-sub">
                              {check.points_earned ?? 0}/{check.points_max ?? 0}
                            </div>
                          </div>
                          <div className="admin-audit-check-message">{formatValue(check.message)}</div>
                          {!check.passed && check.fix && (
                            <div className="admin-fix-box">{check.fix}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 4 - PageSpeed">
        {Object.keys(pagespeed).length ? (
          <>
            <div className="admin-grid admin-form-grid-four">
              <SummaryCard label="Performance" value={formatValue(pagespeed.performance_score, "N/A")} />
              <SummaryCard label="SEO" value={formatValue(pagespeed.seo_score, "N/A")} />
              <SummaryCard label="Accessibility" value={formatValue(pagespeed.accessibility_score, "N/A")} />
              <SummaryCard label="Best Practices" value={formatValue(pagespeed.best_practices_score, "N/A")} />
            </div>
            <SectionFieldGrid
              fields={[
                { label: "LCP", value: pagespeed.lcp },
                { label: "FCP", value: pagespeed.fcp },
                { label: "CLS", value: pagespeed.cls },
                { label: "Speed Index", value: pagespeed.speed_index },
                { label: "Mobile Friendly", value: pagespeed.mobile_friendly },
              ]}
            />
          </>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 5 - Social Media">
        {Object.keys(social).length ? (
          <>
            <div className="admin-stack-list">
              {["facebook", "instagram", "youtube", "linkedin", "twitter", "whatsapp_business"].map((platform) => (
                <div key={platform} className="admin-stack-item">
                  <div className="admin-audit-check-title">
                    <StatusMark passed={Boolean(social[platform])} />
                    <span>{platform}</span>
                  </div>
                  <div className="admin-table-sub">{social[platform] ? "Present" : "Absent"}</div>
                </div>
              ))}
            </div>
            <div className="admin-subsection">
              <h4>Found Platforms</h4>
              {social.found_platforms?.length ? (
                <div className="admin-chip-row">
                  {social.found_platforms.map((platform) => (
                    <span key={platform} className="admin-status-chip">{platform}</span>
                  ))}
                </div>
              ) : (
                <DataNote />
              )}
            </div>
          </>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 6 - SEO Details">
        {Object.keys(seo).length ? (
          <div className="admin-stack">
            <div className="admin-stack-list">
              {(seo.pages || []).length ? (
                seo.pages.map((page, index) => (
                  <div key={`${page.url || "page"}-${index}`} className="admin-panel-card admin-audit-block">
                    <h4>{page.url || `Page ${index + 1}`}</h4>
                    <SectionFieldGrid
                      fields={[
                        { label: "Title", value: page.title },
                        { label: "Meta Description Length", value: page.meta_desc_length },
                        { label: "Meta Description OK", value: page.meta_desc_ok },
                        { label: "H1 Text", value: page.h1_text },
                        { label: "Word Count", value: page.word_count },
                        { label: "Images Missing Alt", value: page.images_missing_alt },
                        { label: "Internal Links", value: page.internal_links },
                      ]}
                    />
                  </div>
                ))
              ) : (
                <DataNote />
              )}
            </div>

            <div className="admin-subsection">
              <h4>Site Level</h4>
              {Object.keys(seo.site_level || {}).length ? (
                <div className="admin-stack-list">
                  {[
                    { label: "robots_txt", value: seo.site_level.has_robots_txt },
                    { label: "sitemap_xml", value: seo.site_level.has_sitemap },
                    { label: "https_everywhere", value: seo.site_level.all_pages_https },
                  ].map((item) => (
                    <div key={item.label} className="admin-stack-item">
                      <div className="admin-audit-check-title">
                        <StatusMark passed={Boolean(item.value)} />
                        <span>{item.label}</span>
                      </div>
                      <div className="admin-table-sub">{item.value ? "Present" : "Absent"}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataNote />
              )}
            </div>

            <div className="admin-grid admin-grid-two">
              <div className="admin-subsection">
                <h4>Issues</h4>
                {(seo.issues || []).length ? (
                  <ul className="admin-bullet-list">
                    {seo.issues.map((item, index) => (
                      <li key={`${item}-${index}`}>{typeof item === "string" ? item : JSON.stringify(item)}</li>
                    ))}
                  </ul>
                ) : (
                  <DataNote />
                )}
              </div>
              <div className="admin-subsection">
                <h4>Recommendations</h4>
                {(seo.recommendations || []).length ? (
                  <ul className="admin-bullet-list">
                    {seo.recommendations.map((item, index) => (
                      <li key={`${item}-${index}`}>{typeof item === "string" ? item : JSON.stringify(item)}</li>
                    ))}
                  </ul>
                ) : (
                  <DataNote />
                )}
              </div>
            </div>
          </div>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 7 - Competitors">
        {Object.keys(competitors).length ? (
          <div className="admin-stack">
            <div className="admin-grid admin-grid-three">
              {[competitors.target, ...(competitors.competitors || [])].filter(Boolean).map((item, index) => (
                <div key={`${item.name || "competitor"}-${index}`} className="admin-summary-card admin-audit-field">
                  <div className="admin-audit-field-value">{formatValue(item.name)}</div>
                  <div className="admin-info-list">
                    <div><strong>Rating:</strong> {formatValue(item.rating)}</div>
                    <div><strong>Review Count:</strong> {formatValue(item.review_count)}</div>
                    <div><strong>Has Website:</strong> {formatValue(item.has_website)}</div>
                    <div><strong>Photos Count:</strong> {formatValue(item.photos_count)}</div>
                    <div><strong>Profile Completeness:</strong> {formatValue(item.profile_completeness)}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="admin-grid admin-grid-two">
              <div className="admin-subsection">
                <h4>Gaps</h4>
                {(competitors.gaps || []).length ? (
                  <ul className="admin-bullet-list">
                    {competitors.gaps.map((gap, index) => (
                      <li key={`${gap.title || gap.label || "gap"}-${index}`}>
                        {gap.title || gap.label || "Gap"}{gap.detail ? `: ${gap.detail}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <DataNote />
                )}
              </div>
              <div className="admin-subsection">
                <h4>AI Summary</h4>
                {competitors.ai_summary ? (
                  <div className="admin-audit-text-block">{competitors.ai_summary}</div>
                ) : (
                  <DataNote />
                )}
              </div>
            </div>
          </div>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 8 - Keywords">
        {Object.keys(keywords).length ? (
          <div className="admin-grid admin-grid-two">
            <div className="admin-subsection">
              <h4>Your Keywords</h4>
              {(keywords.your_keywords || []).length ? (
                <div className="admin-stack-list">
                  {keywords.your_keywords.map((item, index) => (
                    <div key={`${item.keyword}-${index}`} className="admin-stack-item">
                      <div className="admin-table-title">{item.keyword}</div>
                      <div className="admin-table-sub">{item.relevance || "unknown"}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataNote />
              )}
            </div>
            <div className="admin-subsection">
              <h4>Missing Keywords</h4>
              {(keywords.missing_keywords || []).length ? (
                <div className="admin-stack-list">
                  {keywords.missing_keywords.map((item, index) => (
                    <div key={`${item.keyword}-${index}`} className="admin-stack-item admin-opportunity-box">
                      <div className="admin-table-title">{item.keyword}</div>
                      <div className="admin-table-sub">{item.relevance || "unknown"}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataNote />
              )}
            </div>
            <div className="admin-subsection" style={{ gridColumn: "1 / -1" }}>
              <h4>AI Analysis</h4>
              {keywords.ai_analysis ? (
                <div className="admin-audit-text-block">{keywords.ai_analysis}</div>
              ) : (
                <DataNote />
              )}
            </div>
          </div>
        ) : (
          <DataNote />
        )}
      </DetailSection>

      <DetailSection title="Section 9 - Top Fixes">
        {topFixes.length ? (
          <div className="admin-grid admin-grid-three">
            {topFixes.map((item, index) => (
              <div key={`${item.check}-${index}`} className="admin-panel-card admin-audit-block">
                <h4>{item.check || "Fix item"}</h4>
                <div className="admin-audit-text-block">{formatValue(item.fix)}</div>
                <div className="admin-info-list">
                  <div><strong>Service:</strong> {formatValue(item.service)}</div>
                  <div><strong>Impact:</strong> {formatValue(item.impact)}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <DataNote />
        )}
      </DetailSection>
    </div>
  )
}
