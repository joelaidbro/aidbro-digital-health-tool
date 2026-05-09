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

function formatDate(value) {
  if (!value) return ""
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return ""
  return parsed.toLocaleString("en-IN")
}

function averageReviewCount(competitorItems) {
  const counts = (competitorItems || [])
    .map((item) => Number(item?.review_count))
    .filter((value) => Number.isFinite(value))
  if (!counts.length) return null
  return Math.round(counts.reduce((sum, value) => sum + value, 0) / counts.length)
}

function softenTechnicalTerms(text) {
  if (!text) return ""
  return String(text)
    .replace(/canonical tag/gi, "duplicate content protection")
    .replace(/Open Graph tags/gi, "social media preview tags")
    .replace(/schema markup/gi, "Google rich result tags")
    .replace(/meta description/gi, "page description")
}

export default function AuditJsonSections({
  audit,
  manualContactName,
  manualContactPhone,
  manualContactEmail,
  searchDate,
}) {
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
  const weakestPillars = [...pillars]
    .sort((a, b) => (a.percent ?? 0) - (b.percent ?? 0))
    .slice(0, 3)
  const hasManualContact = Boolean(manualContactName || manualContactPhone || manualContactEmail)
  const searchDateText = formatDate(searchDate)
  const competitorAverageReviews = averageReviewCount(competitors.competitors)
  const foundPlatforms = Array.isArray(social.found_platforms) ? social.found_platforms : []
  const absentPlatforms = ["facebook", "instagram", "youtube", "linkedin", "twitter", "whatsapp_business"]
    .filter((platform) => social[platform] === false)

  return (
    <div className="admin-stack">
      <section className="admin-panel-card admin-staff-summary">
        <div className="admin-section-header admin-section-header-tight">
          <div>
            <h4>Staff Contact Summary</h4>
            <p className="admin-muted">Quick read before contacting this client.</p>
          </div>
        </div>

        <div className="admin-grid admin-grid-two admin-staff-summary-grid">
          <div className="admin-stack">
            <div className="admin-staff-summary-head">
              <div>
                <div className="admin-staff-business-name">{business.name || "Business not available"}</div>
                <div className="admin-table-sub">
                  {formatValue(business.category, "Category not available")} · {formatValue(business.location, "Location not available")}
                </div>
              </div>
              <div className={`admin-staff-score-badge ${scoreTone(scoreValue)}`}>
                <span>{score.grade || "-"}</span>
                <strong>{scoreValue}/100</strong>
              </div>
            </div>

            <div className={`admin-staff-google-line ${business.google_profile_found === false ? "is-missing" : ""}`}>
              {business.google_profile_found === false
                ? "Not found on Google"
                : `Google Rating: ${formatValue(business.rating, "-")}★ · ${formatValue(business.total_reviews, "0")} reviews`}
            </div>

            <div className="admin-subsection">
              <h4>Weakest Areas</h4>
              {weakestPillars.length ? (
                <div className="admin-stack-list">
                  {weakestPillars.map((pillar, index) => (
                    <div key={`${pillar.name}-${index}`} className="admin-stack-item">
                      <div className="admin-audit-check-title">
                        <span>{pillar.icon}</span>
                        <span>{pillar.name}</span>
                      </div>
                      <div className="admin-table-sub">{pillar.percent ?? 0}%</div>
                    </div>
                  ))}
                </div>
              ) : (
                <DataNote />
              )}
            </div>
          </div>

          <div className="admin-stack">
            <div className="admin-subsection">
              <h4>Contact Info</h4>
              {(business.phone || business.email || hasManualContact) ? (
                <div className="admin-info-list">
                  {business.phone && <div><strong>Phone:</strong> {business.phone}</div>}
                  {business.email && <div><strong>Email:</strong> {business.email}</div>}
                  {hasManualContact && (
                    <>
                      <div className="admin-summary-label">Manual Contact</div>
                      {manualContactName && <div><strong>Name:</strong> {manualContactName}</div>}
                      {manualContactPhone && <div><strong>Phone:</strong> {manualContactPhone}</div>}
                      {manualContactEmail && <div><strong>Email:</strong> {manualContactEmail}</div>}
                    </>
                  )}
                </div>
              ) : (
                <div className="admin-data-note">No contact info captured yet.</div>
              )}
            </div>

            {topFixes.length > 0 && (
              <div className="admin-subsection">
                <h4>Talk About These</h4>
                <div className="admin-stack-list">
                  {topFixes.slice(0, 2).map((item, index) => (
                    <div key={`${item.check}-${index}`} className="admin-fix-box">
                      <div className="admin-audit-text-block">{formatValue(item.fix)}</div>
                      <div className="admin-table-sub">{formatValue(item.service, "Service not set")}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {searchDateText && (
              <div className="admin-staff-search-date">
                Search date: {searchDateText}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="admin-panel-card admin-analyst-briefing">
        <div className="admin-section-header admin-section-header-tight">
          <div>
            <h4>Analyst Briefing</h4>
            <p className="admin-muted">Business-friendly talking points for your call.</p>
          </div>
        </div>

        <div className="admin-stack">
          <div className="admin-briefing-block">
            <div className="admin-briefing-label">Google Presence</div>
            <div className="admin-audit-text-block">
              {business.google_profile_found
                ? (
                  <>
                    {`Found on Google with a ${formatValue(business.rating, "-")}★ rating and ${formatValue(business.total_reviews, "0")} reviews.`}
                    {competitorAverageReviews !== null && Number.isFinite(Number(business.total_reviews)) && competitorAverageReviews > Number(business.total_reviews)
                      ? ` Competitors in this category average ${competitorAverageReviews} reviews — there is a review gap to close.`
                      : ""}
                  </>
                )
                : "This business has no Google listing — a critical gap that should be the first talking point."}
            </div>
          </div>

          <div className="admin-briefing-block">
            <div className="admin-briefing-label">Website Health</div>
            {Object.keys(pagespeed).length ? (
              <div className="admin-stack">
                <div className="admin-audit-text-block">
                  {`Website loads in ${formatValue(pagespeed.lcp, "not available")} on mobile with a performance score of ${formatValue(pagespeed.performance_score, "0")}/100.`}
                  {Number.isFinite(Number(pagespeed.performance_score))
                    ? Number(pagespeed.performance_score) < 50
                      ? " This is significantly slower than recommended and likely losing visitors."
                      : Number(pagespeed.performance_score) <= 75
                        ? " There is room for improvement."
                        : " Performance is solid."
                    : ""}
                </div>
                {Array.isArray(seo.issues) && seo.issues.length > 0 && (
                  <div>
                    <div className="admin-audit-text-block">Key issues found:</div>
                    <ul className="admin-bullet-list">
                      {seo.issues
                        .filter((item) => {
                          if (typeof item === "string") return true
                          return item?.severity === "warning" || item?.severity === "error"
                        })
                        .map((item, index) => {
                          const issueText = typeof item === "string"
                            ? softenTechnicalTerms(item)
                            : softenTechnicalTerms(item?.issue)
                          const fixText = typeof item === "string"
                            ? ""
                            : softenTechnicalTerms(item?.fix)

                          if (!issueText) return null

                          return (
                            <li key={`${issueText}-${index}`}>
                              <div>{issueText}</div>
                              {fixText && (
                                <div className="admin-table-sub">How to fix: {fixText}</div>
                              )}
                            </li>
                          )
                        })}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="admin-audit-text-block">Website performance data was not available for this business.</div>
            )}
          </div>

          {Object.keys(social).length > 0 && (
            <div className="admin-briefing-block">
              <div className="admin-briefing-label">Social Media</div>
              <div className="admin-stack">
                {absentPlatforms.length > 0 && (
                  <ul className="admin-bullet-list">
                    {absentPlatforms.map((platform) => (
                      <li key={platform}>{`No ${platform} presence detected.`}</li>
                    ))}
                  </ul>
                )}
                <div className="admin-audit-text-block">
                  {absentPlatforms.length === 0
                    ? "Strong social media presence across all major platforms."
                    : `Currently active on ${foundPlatforms.join(", ")}.`}
                </div>
              </div>
            </div>
          )}

          <div className="admin-briefing-block">
            <div className="admin-briefing-label">Reputation vs Competitors</div>
            {Object.keys(competitors).length ? (
              <div className="admin-stack">
                <div className="admin-audit-text-block">
                  {`This business has ${formatValue(competitors.target?.review_count, "0")} reviews.`}
                  {competitorAverageReviews !== null ? ` Nearby competitors average ${competitorAverageReviews} reviews.` : ""}
                </div>
                {Array.isArray(competitors.gaps) && competitors.gaps.length > 0 && (
                  <ul className="admin-bullet-list">
                    {competitors.gaps.map((gap, index) => (
                      <li key={`${gap.title || gap.label || "gap"}-${index}`}>
                        {gap.title || gap.label || "Gap"}{gap.detail ? `: ${gap.detail}` : ""}
                      </li>
                    ))}
                  </ul>
                )}
                {competitors.ai_summary && (
                  <div className="admin-audit-text-block">{competitors.ai_summary}</div>
                )}
              </div>
            ) : (
              <div className="admin-audit-text-block">Competitor data was not available for this search.</div>
            )}
          </div>

          {Object.keys(keywords).length > 0 && (
            <div className="admin-briefing-block">
              <div className="admin-briefing-label">Search Visibility Opportunities</div>
              <div className="admin-stack">
                {Array.isArray(keywords.missing_keywords) && keywords.missing_keywords.length > 0 && (
                  <div>
                    <div className="admin-audit-text-block">
                      Topics competitors are ranking for that this business is missing:
                    </div>
                    <ul className="admin-bullet-list">
                      {keywords.missing_keywords.map((item, index) => (
                        <li key={`${item.keyword}-${index}`}>
                          {item.keyword}{item.relevance ? ` — ${item.relevance}` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {keywords.ai_analysis && (
                  <div className="admin-audit-text-block">{keywords.ai_analysis}</div>
                )}
              </div>
            </div>
          )}

          {topFixes.length > 0 && (
            <div className="admin-briefing-block">
              <div className="admin-briefing-label">Quick Wins</div>
              <ul className="admin-bullet-list">
                {topFixes.map((item, index) => (
                  <li key={`${item.check}-${index}`}>
                    {index === 0 && <span className="admin-high-impact-tag">Highest Impact</span>}{" "}
                    {`${formatValue(item.fix)} — relates to ${formatValue(item.service, "Not available")}.`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

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
