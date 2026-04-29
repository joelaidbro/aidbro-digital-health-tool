function asArray(value) {
  return Array.isArray(value) ? value : []
}

function hasValue(value) {
  return !(value === null || value === undefined || value === "")
}

function asText(value, fallback = "-") {
  if (!hasValue(value)) {
    return fallback
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value)
  }
  if (Array.isArray(value)) {
    const compact = value
      .map((item) => asText(item, ""))
      .filter(Boolean)
      .join(", ")
    return compact || fallback
  }
  if (typeof value === "object") {
    const primary =
      value.text ||
      value.label ||
      value.name ||
      value.title ||
      value.keyword ||
      value.summary ||
      value.message ||
      value.fix ||
      value.issue
    if (primary) {
      return asText(primary, fallback)
    }
    try {
      return JSON.stringify(value)
    } catch {
      return fallback
    }
  }
  return fallback
}

function recommendationText(recommendation) {
  return asText(recommendation, "Recommendation available")
}

function fixLabel(fix) {
  if (!fix || typeof fix !== "object") {
    return "Priority fix"
  }
  return asText(fix.check || fix.title || fix.issue, "Priority fix")
}

function fixText(fix) {
  if (!fix || typeof fix !== "object") {
    return asText(fix, "Review this issue")
  }
  return asText(fix.fix || fix.recommendation || fix.action || fix.summary, "Review this issue")
}

function gapLabel(gap) {
  if (!gap || typeof gap !== "object") {
    return "Gap"
  }
  return asText(gap.dimension || gap.category || gap.name, "Gap")
}

function gapText(gap) {
  if (!gap || typeof gap !== "object") {
    return asText(gap, "Gap detected")
  }
  return asText(gap.insight || gap.summary || gap.message, "Gap detected")
}

function keywordLabel(keyword) {
  if (!keyword || typeof keyword !== "object") {
    return asText(keyword, "Keyword")
  }
  return asText(keyword.keyword || keyword.label || keyword.term, "Keyword")
}

function SummaryCard({ label, value, hint = "" }) {
  return (
    <div className="admin-summary-card">
      <div className="admin-summary-label">{label}</div>
      <div className="admin-summary-value">{asText(value)}</div>
      {hint && <div className="admin-metric-hint">{hint}</div>}
    </div>
  )
}

function SocialPill({ label, active }) {
  return (
    <div
      className="admin-tab"
      style={{
        cursor: "default",
        opacity: active ? 1 : 0.75,
        borderColor: active ? "rgba(249, 115, 22, 0.6)" : "var(--border-dim)",
      }}
    >
      {active ? "Yes" : "-"} {label}
    </div>
  )
}

export default function SearchAuditSnapshot({
  search,
  audit,
  title = "Search Snapshot",
}) {
  if (!audit || typeof audit !== "object" || !Object.keys(audit).length) {
    return (
      <div className="admin-subsection">
        <h4>{title}</h4>
        <div className="admin-muted">No stored audit snapshot was found for this search.</div>
      </div>
    )
  }

  const business = audit.business || {}
  const score = audit.score || {}
  const pagespeed = audit.pagespeed || {}
  const social = audit.social || {}
  const seo = audit.seo || {}
  const competitors = audit.competitors || {}
  const keywords = audit.keywords || {}
  const insights = audit.insights || {}
  const topFixes = asArray(score.top_fixes)
  const pillars = asArray(Object.values(score.pillars || {}))
  const seoChecks = asArray(seo.checks)
  const seoPassed = seoChecks.filter((check) => check?.passed).length
  const seoFailed = seoChecks.filter((check) => check && !check.passed).length
  const competitorRows = asArray(competitors.competitors)
  const missingKeywords = asArray(keywords.missing_keywords)
  const gapRows = asArray(competitors.gaps)
  const seoRecommendations = asArray(seo.recommendations)

  return (
    <div className="admin-subsection">
      <h4>{title}</h4>

      {!!business.google_match_warning && (
        <div
          style={{
            marginBottom: 16,
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(249, 115, 22, 0.35)",
            background: "rgba(249, 115, 22, 0.08)",
            color: "var(--white)",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          <strong>
            {business.google_match_confidence === "medium"
              ? "Google profile check:"
              : "Google profile not confirmed:"}
          </strong>{" "}
          {asText(business.google_match_warning)}
        </div>
      )}

      <div className="admin-grid admin-grid-three">
        <SummaryCard label="Total Score" value={score.total_score ? `${score.total_score}/100` : "-"} />
        <SummaryCard
          label="Grade"
          value={score.grade ? `${score.grade}${score.label ? ` - ${score.label}` : ""}` : "-"}
        />
        <SummaryCard
          label="Website Speed"
          value={pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A"}
        />
      </div>

      <div className="admin-grid admin-grid-three">
        <SummaryCard
          label="Google Rating"
          value={business.rating ? `${business.rating} (${business.total_reviews || 0})` : "Not detected"}
        />
        <SummaryCard label="Social Platforms" value={social.social_count ?? 0} />
        <SummaryCard label="Competitors" value={competitorRows.length} />
      </div>

      <div className="admin-info-list">
        <div><strong>Business:</strong> {asText(business.name || search?.business_name)}</div>
        <div><strong>Location:</strong> {asText(business.location || search?.location)}</div>
        <div><strong>Category:</strong> {asText(business.category || search?.category || "General Business")}</div>
        <div><strong>Address:</strong> {asText(business.address, "Not captured")}</div>
        <div><strong>Website:</strong> {asText(business.website || search?.website_url, "Not detected")}</div>
        <div><strong>Phone:</strong> {asText(business.phone || search?.manual_contact_phone || search?.auto_phone, "Not captured")}</div>
        <div><strong>Email:</strong> {asText(business.email || search?.manual_contact_email || search?.auto_email, "Not captured")}</div>
      </div>

      {hasValue(insights.summary) && (
        <div className="admin-subsection">
          <h4>AI Summary</h4>
          <div className="admin-info-list">
            <div>{asText(insights.summary)}</div>
            {hasValue(insights.insight) && <div>{asText(insights.insight)}</div>}
            {hasValue(insights.cta) && <div><strong>CTA:</strong> {asText(insights.cta)}</div>}
          </div>
        </div>
      )}

      {!!pillars.length && (
        <div className="admin-subsection">
          <h4>Pillar Breakdown</h4>
          <div className="admin-grid admin-grid-two">
            {pillars.map((pillar, index) => (
              <SummaryCard
                key={`${asText(pillar?.name, "pillar")}-${index}`}
                label={asText(pillar?.name, "Pillar")}
                value={`${asText(pillar?.score, "0")}/${asText(pillar?.max, "0")}`}
                hint={`${asText(pillar?.percent, "0")}% complete`}
              />
            ))}
          </div>
        </div>
      )}

      <div className="admin-subsection">
        <h4>Social Presence</h4>
        <div className="admin-chip-row">
          <SocialPill label="Instagram" active={!!social.instagram} />
          <SocialPill label="Facebook" active={!!social.facebook} />
          <SocialPill label="LinkedIn" active={!!social.linkedin} />
          <SocialPill label="YouTube" active={!!social.youtube} />
          <SocialPill label="Twitter / X" active={!!social.twitter} />
          <SocialPill label="WhatsApp" active={!!social.whatsapp_business} />
        </div>
      </div>

      <div className="admin-subsection">
        <h4>Website and SEO</h4>
        <div className="admin-grid admin-grid-three">
          <SummaryCard label="Performance" value={pagespeed.performance_score ? `${pagespeed.performance_score}/100` : "N/A"} />
          <SummaryCard label="SEO Score" value={pagespeed.seo_score ? `${pagespeed.seo_score}/100` : "N/A"} />
          <SummaryCard label="HTTPS" value={pagespeed.is_https ? "Secure" : "Not secure"} />
        </div>
        <div className="admin-grid admin-grid-three">
          <SummaryCard label="LCP" value={pagespeed.lcp || "N/A"} />
          <SummaryCard label="CLS" value={pagespeed.cls || "N/A"} />
          <SummaryCard label="SEO Checks" value={`${seoPassed} passed / ${seoFailed} failed`} />
        </div>
        {!!seoRecommendations.length && (
          <ul className="admin-bullet-list">
            {seoRecommendations.slice(0, 5).map((recommendation, index) => (
              <li key={`${recommendationText(recommendation)}-${index}`}>
                {recommendationText(recommendation)}
              </li>
            ))}
          </ul>
        )}
      </div>

      {!!topFixes.length && (
        <div className="admin-subsection">
          <h4>Top Priority Fixes</h4>
          <ul className="admin-bullet-list">
            {topFixes.slice(0, 5).map((fix, index) => (
              <li key={`${fixLabel(fix)}-${index}`}>
                <strong>{fixLabel(fix)}:</strong> {fixText(fix)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!!competitorRows.length && (
        <div className="admin-subsection">
          <h4>Competitors</h4>
          <div className="admin-stack-list">
            {competitorRows.slice(0, 5).map((competitor, index) => (
              <div key={`${asText(competitor?.name, "competitor")}-${index}`} className="admin-stack-item">
                <div>
                  <div className="admin-table-title">{asText(competitor?.name, "Competitor")}</div>
                  <div className="admin-table-sub">{asText(competitor?.website_url, "No website detected")}</div>
                </div>
                <div className="admin-table-sub">
                  {competitor?.rating
                    ? `${asText(competitor.rating)} - ${asText(competitor.review_count || 0)} reviews`
                    : "No rating"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!!gapRows.length && (
        <div className="admin-subsection">
          <h4>Competitive Gaps</h4>
          <ul className="admin-bullet-list">
            {gapRows.slice(0, 5).map((gap, index) => (
              <li key={`${gapLabel(gap)}-${index}`}>
                <strong>{gapLabel(gap)}:</strong> {gapText(gap)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!!missingKeywords.length && (
        <div className="admin-subsection">
          <h4>Missing Keywords</h4>
          <div className="admin-chip-row">
            {missingKeywords.slice(0, 10).map((keyword, index) => (
              <div key={`${keywordLabel(keyword)}-${index}`} className="admin-tab" style={{ cursor: "default" }}>
                {keywordLabel(keyword)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
