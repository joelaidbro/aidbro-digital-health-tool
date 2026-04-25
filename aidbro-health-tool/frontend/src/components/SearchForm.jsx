import { useState } from "react"
import { useAuth } from "../context/AuthContext"

const BUSINESS_CATEGORIES = [
  { group: "Local Services", options: [
    "Retail / Shop",
    "Restaurant / Food & Beverage",
    "Clinic / Healthcare",
    "Salon & Beauty",
    "Gym & Fitness",
    "Hotel & Hospitality",
    "Jewellery & Gold",
    "Pharmacy",
    "Automobile / Garage",
    "Supermarket / Grocery",
    "Electronics Store",
    "Furniture & Home Décor",
    "Clothing & Apparel",
  ]},
  { group: "Professional Services", options: [
    "IT / Software Company",
    "Education / Coaching Centre",
    "Real Estate",
    "Legal / Advocate",
    "Chartered Accountant / Finance",
    "Architect / Interior Design",
    "Event Management",
    "Photography / Studio",
    "Advertising / Marketing Agency",
    "Consulting / Business Services",
  ]},
  { group: "Industry & Trade", options: [
    "Manufacturing",
    "Construction",
    "Textile / Garments",
    "Agriculture / Farm",
    "Export / Import",
    "Logistics / Transport",
    "Printing & Packaging",
    "Wholesale / Distribution",
  ]},
  { group: "Other", options: [
    "E-commerce / Online Store",
    "NGO / Trust / Charity",
    "Government / PSU",
    "General Business",
  ]},
]

const SOCIAL_PLATFORMS = [
  {
    key: "instagram_url",
    label: "INSTAGRAM",
    icon: "📸",
    placeholder: "https://instagram.com/yourbusiness",
    color: "#E1306C",
  },
  {
    key: "facebook_url",
    label: "FACEBOOK",
    icon: "📘",
    placeholder: "https://facebook.com/yourbusiness",
    color: "#1877F2",
  },
  {
    key: "linkedin_url",
    label: "LINKEDIN",
    icon: "💼",
    placeholder: "https://linkedin.com/company/yourbusiness",
    color: "#0A66C2",
  },
]

export default function SearchForm({ onSearch }) {
  const { isAuthenticated, isPaid } = useAuth()
  const [businessName, setBusinessName] = useState("")
  const [location, setLocation]         = useState("")
  const [category, setCategory]         = useState("")
  const [websiteUrl, setWebsiteUrl]     = useState("")
  const [instagramUrl, setInstagramUrl] = useState("")
  const [facebookUrl, setFacebookUrl]   = useState("")
  const [linkedinUrl, setLinkedinUrl]   = useState("")
  const [showSocial, setShowSocial]     = useState(false)
  const [loading, setLoading]           = useState(false)
  const [errors, setErrors]             = useState({})

  const validate = () => {
    const e = {}
    if (!businessName.trim()) e.businessName = "Business name is required"
    if (!location.trim())     e.location     = "City / area is required"
    if (!category)            e.category     = "Please select a business category"
    return e
  }

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    const e = validate()
    if (Object.keys(e).length) { setErrors(e); return }
    setErrors({})
    setLoading(true)
    await onSearch({
      businessName,
      location,
      category,
      websiteUrl,
      instagramUrl,
      facebookUrl,
      linkedinUrl,
    })
    setLoading(false)
  }

  const socialFilled = [instagramUrl, facebookUrl, linkedinUrl].filter(Boolean).length

  return (
    <div className="search-page">

      {/* Navbar */}
      <nav className="navbar">
        <a href="#" className="navbar-logo">
          Aidbro <span>AI</span>
          <span className="navbar-badge">Digital Health Tool</span>
        </a>
        <div className="navbar-links">
          <a href="https://realsdigitalinnovations.com" target="_blank" rel="noreferrer">
            About Aidbro
          </a>
          <a href="https://realsdigitalinnovations.com/contact.php" target="_blank" rel="noreferrer">
            Contact
          </a>
          {isAuthenticated ? (
            <a
              href="/portal"
              className="btn-primary"
              style={{ padding: "8px 18px", fontSize: "13px" }}
            >
              {isPaid ? "My Reports" : "My Searches"}
            </a>
          ) : (
            <>
              <a href="/auth">Login</a>
              <a
                href="/register"
                className="btn-primary"
                style={{ padding: "8px 18px", fontSize: "13px" }}
              >
                Sign Up
              </a>
            </>
          )}
          <a
            href="https://wa.me/918589999362"
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
            style={{ padding: "8px 18px", fontSize: "13px" }}
          >
            WhatsApp Us
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-inner">

          <div className="hero-badge fade-up">
            <span className="dot" />
            FREE · No Sign-up Required · 60 Second Audit
          </div>

          <h1 className="fade-up-d1">
            How Strong Is Your<br />
            <em>Digital Presence?</em>
          </h1>

          <p className="fade-up-d2">
            Enter your business details and get an AI-powered Digital Health Score —
            a full audit of your Google listing, website, social media, and reputation
            vs. local competitors. Works for any business across world.
          </p>

          <div className="hero-returning-actions fade-up-d2">
            {isAuthenticated ? (
              <a href="/portal" className="btn-primary">
                {isPaid ? "Open My Reports" : "Open My Searches"}
              </a>
            ) : (
              <>
                <a href="/auth" className="btn-secondary">
                  Already have an account? Login
                </a>
                <a href="/register" className="btn-primary">
                  Sign Up Free
                </a>
              </>
            )}
          </div>

          {/* Form Card */}
          <div className="search-card fade-up-d3">
            <p className="search-card-title">ANALYZE YOUR BUSINESS</p>

            <form onSubmit={handleSubmit} noValidate>

              {/* Row 1 — Name + Location */}
              <div className="form-row">
                <div className="form-field">
                  <label>BUSINESS NAME *</label>
                  <input
                    type="text"
                    placeholder="e.g. Grand Silks, Apollo Clinic"
                    value={businessName}
                    onChange={(e) => {
                      setBusinessName(e.target.value)
                      setErrors((v) => ({ ...v, businessName: "" }))
                    }}
                    autoFocus
                  />
                  <span className="field-help">
                    Enter the business name as accurately as possible for better Google profile matching.
                  </span>
                  {errors.businessName && (
                    <span className="field-error">{errors.businessName}</span>
                  )}
                </div>
                <div className="form-field">
                  <label>CITY / AREA *</label>
                  <input
                    type="text"
                    placeholder="e.g. Kannur, Mumbai, Bangalore"
                    value={location}
                    onChange={(e) => {
                      setLocation(e.target.value)
                      setErrors((v) => ({ ...v, location: "" }))
                    }}
                  />
                  {errors.location && (
                    <span className="field-error">{errors.location}</span>
                  )}
                </div>
              </div>

              {/* Row 2 — Category */}
              <div className="form-row single">
                <div className="form-field">
                  <label>BUSINESS CATEGORY *</label>
                  <select
                    value={category}
                    onChange={(e) => {
                      setCategory(e.target.value)
                      setErrors((v) => ({ ...v, category: "" }))
                    }}
                    className="form-select"
                  >
                    <option value="">— Select your business type —</option>
                    {BUSINESS_CATEGORIES.map((group) => (
                      <optgroup key={group.group} label={`── ${group.group}`}>
                        {group.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                  {errors.category && (
                    <span className="field-error">{errors.category}</span>
                  )}
                </div>
              </div>

              {/* Row 3 — Website */}
              <div className="form-row single">
                <div className="form-field">
                  <label>
                    WEBSITE URL{" "}
                    <span className="optional-tag">optional</span>
                  </label>
                  <input
                    type="url"
                    placeholder="https://yourbusiness.com"
                    value={websiteUrl}
                    onChange={(e) => setWebsiteUrl(e.target.value)}
                  />
                </div>
              </div>

              {/* Social handles — collapsible */}
              <button
                type="button"
                className="social-toggle"
                onClick={() => setShowSocial((v) => !v)}
              >
                <span className="social-toggle-icons">📸 📘 💼</span>
                <span>Add Social Media Handles</span>
                {socialFilled > 0 && (
                  <span className="social-count-badge">
                    {socialFilled} added
                  </span>
                )}
                <span className="social-toggle-arrow">
                  {showSocial ? "▲" : "▼"}
                </span>
              </button>

              {showSocial && (
                <div className="social-fields">
                  <p className="social-fields-hint">
                    💡 Adding your handles lets us verify your presence directly
                    — much more accurate than auto-detection. Leave blank if
                    not applicable to your business.
                  </p>
                  {SOCIAL_PLATFORMS.map((platform) => {
                    const val =
                      platform.key === "instagram_url" ? instagramUrl :
                      platform.key === "facebook_url"  ? facebookUrl  :
                      linkedinUrl
                    const setter =
                      platform.key === "instagram_url" ? setInstagramUrl :
                      platform.key === "facebook_url"  ? setFacebookUrl  :
                      setLinkedinUrl
                    return (
                      <div className="form-field social-field" key={platform.key}>
                        <label>
                          <span
                            className="platform-dot"
                            style={{ background: platform.color }}
                          />
                          {platform.icon} {platform.label}
                          <span className="optional-tag">optional</span>
                        </label>
                        <div className="social-input-wrap">
                          <input
                            type="url"
                            placeholder={platform.placeholder}
                            value={val}
                            onChange={(e) => setter(e.target.value)}
                          />
                          {val && (
                            <span className="social-check-badge">✓</span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Submit */}
              <div className="form-submit">
                <button
                  className="btn-primary"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span
                        style={{
                          display: "inline-block",
                          animation: "spin 0.8s linear infinite",
                        }}
                      >
                        ⏳
                      </span>
                      Analyzing...
                    </>
                  ) : (
                    <>🔍 Get My Free Digital Health Score</>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Trust badges */}
          <div className="trust-row fade-up-d4">
            {[
              ["🔒", "100% Free"],
              ["⚡", "60 Second Results"],
              ["📊", "5 Audit Pillars"],
              ["🤖", "AI-Powered Report"],
              ["🇮🇳", "India-Wide"],
            ].map(([icon, text]) => (
              <div key={text} className="trust-item">
                <span className="ti-icon">{icon}</span>
                {text}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
