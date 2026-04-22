import { useState } from "react"

const API = "http://localhost:8000/api"

const PLATFORMS = [
  { key: "instagram", label: "Instagram",  icon: "📸", placeholder: "https://instagram.com/yourbusiness",  color: "#E1306C" },
  { key: "facebook",  label: "Facebook",   icon: "📘", placeholder: "https://facebook.com/yourbusiness",   color: "#1877F2" },
  { key: "linkedin",  label: "LinkedIn",   icon: "💼", placeholder: "https://linkedin.com/company/yourbusiness", color: "#0A66C2" },
  { key: "youtube",   label: "YouTube",    icon: "▶️", placeholder: "https://youtube.com/@yourbusiness",  color: "#FF0000" },
  { key: "twitter",   label: "Twitter / X",icon: "🐦", placeholder: "https://twitter.com/yourbusiness",   color: "#1DA1F2" },
]

export default function SocialImprove({ currentSocial, businessName, location, category, websiteUrl, onScoreUpdate }) {
  const [links, setLinks]   = useState({})
  const [loading, setLoading] = useState(false)
  const [applied, setApplied] = useState(false)
  const [error, setError]   = useState("")

  // Pre-fill any already-detected platforms
  const alreadyFound = Object.keys(currentSocial || {}).filter(
    k => currentSocial[k] === true && PLATFORMS.find(p => p.key === k)
  )

  const hasNewLinks = Object.values(links).some(v => v.trim())

  const handleApply = async () => {
    if (!hasNewLinks) return
    setLoading(true)
    setError("")
    try {
      const res = await fetch(`${API}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name:  businessName,
          location:       location,
          category:       category,
          website_url:    websiteUrl || "",
          instagram_url:  links.instagram  || "",
          facebook_url:   links.facebook   || "",
          linkedin_url:   links.linkedin   || "",
          youtube_url:    links.youtube    || "",
          twitter_url:    links.twitter    || "",
        }),
      })
      if (!res.ok) throw new Error("Could not re-run audit")
      const data = await res.json()
      setApplied(true)
      onScoreUpdate?.(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (applied) {
    return (
      <div className="social-improve-card social-improve-success">
        <span>✅</span>
        <p>Social media links verified! Your score has been updated.</p>
      </div>
    )
  }

  return (
    <div className="social-improve-card social-improve-card-inline">
      <div className="social-improve-header">
        <div className="social-improve-icon">🔗</div>
        <div className="social-improve-toggle-text">
          <strong>Add your official social links</strong>
          <span>
            Paste the links below and we'll verify them by running the audit again.
            Instagram, Facebook, and LinkedIn affect the score directly. YouTube and
            X/Twitter will still appear in the audit even though they do not add score points yet.
          </span>
        </div>
        <div className="social-improve-badge">Quick update</div>
      </div>

      <div className="social-improve-body social-improve-body-open">
        {alreadyFound.length > 0 && (
          <p className="social-improve-found">
            ✅ Already detected: {alreadyFound.map(k =>
              PLATFORMS.find(p=>p.key===k)?.label
            ).filter(Boolean).join(", ")}
          </p>
        )}

        <div className="social-improve-fields">
          {PLATFORMS.map(platform => {
            const alreadyDetected = currentSocial?.[platform.key] === true
            return (
              <div key={platform.key} className="social-improve-field">
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span className="kw-dot" style={{ background: platform.color }} />
                  {platform.icon} {platform.label}
                  {alreadyDetected && (
                    <span className="social-improve-detected">auto-detected</span>
                  )}
                </label>
                <input
                  type="url"
                  placeholder={platform.placeholder}
                  value={links[platform.key] || ""}
                  onChange={e => setLinks(v => ({ ...v, [platform.key]: e.target.value }))}
                  disabled={alreadyDetected}
                  style={{ opacity: alreadyDetected ? 0.5 : 1 }}
                />
              </div>
            )
          })}
        </div>

        {error && <p style={{ color: "var(--red)", fontSize: 12 }}>{error}</p>}

        <button
          className="btn-primary"
          onClick={handleApply}
          disabled={loading || !hasNewLinks}
          style={{ width: "100%", justifyContent: "center" }}
        >
          {loading ? "⏳ Verifying & updating score..." : "✓ Apply Links & Update Score"}
        </button>
      </div>
    </div>
  )
}
