import { useState, useEffect } from "react"

import { API } from "../config/api"

export default function ContactCapture({ leadId, businessName, score }) {
  const [visible, setVisible]   = useState(false)
  const [dismissed, setDismissed] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [name, setName]         = useState("")
  const [phone, setPhone]       = useState("")
  const [email, setEmail]       = useState("")
  const [error, setError]       = useState("")

  // ── Trigger: show after 5s OR after 70% scroll, whichever first ───────────
  useEffect(() => {
    if (dismissed || submitted) return

    // Timer trigger
    const timer = setTimeout(() => setVisible(true), 5000)

    // Scroll trigger
    const handleScroll = () => {
      const scrollPct =
        (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight
      if (scrollPct >= 0.7) setVisible(true)
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => {
      clearTimeout(timer)
      window.removeEventListener("scroll", handleScroll)
    }
  }, [dismissed, submitted])

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!name.trim() && !phone.trim() && !email.trim()) {
      setError("Please fill at least one field.")
      return
    }
    if (!leadId) {
      setError("Something went wrong. Please try again.")
      return
    }

    setError("")
    setLoading(true)

    try {
      const res = await fetch(`${API}/leads/${leadId}/contact`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lead_id:       leadId,
          contact_name:  name.trim()  || null,
          contact_phone: phone.trim() || null,
          contact_email: email.trim() || null,
        }),
      })
      if (!res.ok) throw new Error("Failed to save")
      setSubmitted(true)
    } catch {
      setError("Could not save. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (!visible || dismissed) return null

  // ── Submitted state ───────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div className="cc-backdrop" onClick={() => setDismissed(true)}>
        <div className="cc-card cc-card--success" onClick={(e) => e.stopPropagation()}>
          <button className="cc-close" onClick={() => setDismissed(true)}>✕</button>
          <div className="cc-success-icon">✅</div>
          <h3 className="cc-title">We'll be in touch!</h3>
          <p className="cc-sub">
            The Aidbro team will reach out via WhatsApp shortly to discuss
            improving your <strong style={{ color: "var(--orange)" }}>{score}/100</strong> score.
          </p>
          <a
            href={`https://wa.me/918589999362?text=Hi! I just checked the digital health score for ${encodeURIComponent(businessName || "my business")} and got ${score}/100. I'd like to know more.`}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
          >
            💬 Chat on WhatsApp Now
          </a>
        </div>
      </div>
    )
  }

  // ── Main form ─────────────────────────────────────────────────────────────
  return (
    <div className="cc-backdrop" onClick={() => setDismissed(true)}>
      <div className="cc-card" onClick={(e) => e.stopPropagation()}>
        <button className="cc-close" onClick={() => setDismissed(true)}>✕</button>

        <div className="cc-header">
          <span className="cc-emoji">📞</span>
          <div>
            <h3 className="cc-title">Want us to fix this?</h3>
            <p className="cc-sub">
              Your score is{" "}
              <strong style={{ color: score >= 70 ? "var(--green)" : score >= 50 ? "var(--yellow)" : "var(--red)" }}>
                {score}/100
              </strong>
              . Leave your details — Aidbro will reach out today.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="cc-fields">
            <div className="cc-field">
              <label>NAME</label>
              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="cc-field">
              <label>WHATSAPP NUMBER</label>
              <input
                type="tel"
                placeholder="+91 98765 43210"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
            <div className="cc-field">
              <label>EMAIL</label>
              <input
                type="email"
                placeholder="you@business.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          {error && <p className="cc-error">{error}</p>}

          <p className="cc-hint">All fields are optional. We'll never spam.</p>

          <div className="cc-actions">
            <button
              type="button"
              className="btn-ghost"
              onClick={() => setDismissed(true)}
            >
              Skip
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ flex: 1, justifyContent: "center" }}
            >
              {loading ? "Saving..." : "Send to Aidbro →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
