import { useState } from "react"
import { useAuth } from "../context/AuthContext"
import { API } from "../config/api"
import { useCreditConfig } from "../config/creditConfig"
import SiteLogo from "../components/SiteLogo"

export default function BuyCreditsPage({ onSuccess }) {
  const { user, authFetch, updateCredits } = useAuth()
  const { price_inr, credits_per_purchase, formatted } = useCreditConfig()
  const [paying, setPaying] = useState(false)
  const [error, setError] = useState("")
  const [confirmed, setConfirmed] = useState(null)

  const credits = user?.audit_credits ?? 0
  const isTest  = user?.is_test_account ?? false

  const handleBuy = async () => {
    setError("")
    setPaying(true)

    try {
      const orderRes = await authFetch(`${API}/payment/credits/create-order`, {
        method: "POST",
      })
      const orderData = await orderRes.json()
      if (!orderRes.ok) {
        throw new Error(orderData.detail || "Could not create order.")
      }

      if (!window.Razorpay) {
        await new Promise((resolve, reject) => {
          const script = document.createElement("script")
          script.src = "https://checkout.razorpay.com/v1/checkout.js"
          script.onload = resolve
          script.onerror = reject
          document.head.appendChild(script)
        })
      }

      const rzp = new window.Razorpay({
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "Aidbro",
        description: orderData.description,
        order_id: orderData.order_id,
        prefill: {
          email: orderData.prefill_email,
          name: user?.name || "",
        },
        theme: { color: "#FF6B00" },
        modal: {
          ondismiss: () => setPaying(false),
        },
        handler: async (response) => {
          try {
            const verifyRes = await authFetch(`${API}/payment/credits/verify`, {
              method: "POST",
              body: JSON.stringify({
                razorpay_order_id:   response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature:  response.razorpay_signature,
              }),
            })
            const verifyData = await verifyRes.json()
            if (!verifyRes.ok) {
              throw new Error(verifyData.detail || "Verification failed.")
            }

            updateCredits(verifyData.total_credits)
            setConfirmed({
              credits_added: verifyData.credits_added,
              total_credits: verifyData.total_credits,
            })
          } catch (err) {
            setError(err.message || "Payment verification failed.")
          } finally {
            setPaying(false)
          }
        },
      })

      rzp.open()
    } catch (err) {
      setError(err.message || "Payment failed. Please try again.")
      setPaying(false)
    }
  }

  return (
    <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column" }}>

      {/* Top bar */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 24px",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(6,13,31,0.6)", backdropFilter: "blur(10px)",
      }}>
        <a href="/" style={{ display: "flex", alignItems: "center" }}>
          <SiteLogo compact />
        </a>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {(credits > 0 || isTest) && (
            <>
              <a
                href="/portal"
                style={{ color: "#c7ccdd", fontSize: 14, fontWeight: 600, padding: "8px 14px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.12)" }}
              >
                My Searches
              </a>
              <a
                href="/app"
                className="btn-primary"
                style={{ padding: "8px 18px", fontSize: 14 }}
              >
                Run Audit →
              </a>
            </>
          )}
          {credits === 0 && !isTest && (
            <a href="/portal" style={{ color: "#c7ccdd", fontSize: 14, fontWeight: 600 }}>
              My Account
            </a>
          )}
        </div>
      </div>

      {/* Confirmation modal */}
      {confirmed && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 9999,
          background: "rgba(0,0,0,0.7)", backdropFilter: "blur(6px)",
          display: "flex", alignItems: "center", justifyContent: "center",
          padding: 24,
        }}>
          <div style={{
            background: "#0f1b3d", border: "1px solid rgba(255,255,255,0.14)",
            borderRadius: 20, padding: "40px 32px", maxWidth: 420, width: "100%",
            textAlign: "center", boxShadow: "0 24px 60px rgba(0,0,0,0.5)",
          }}>
            <div style={{ fontSize: "3rem", marginBottom: 16 }}>✅</div>
            <h2 style={{ color: "#fff", marginBottom: 10, fontSize: "1.4rem" }}>
              Payment Successful!
            </h2>
            <p style={{ color: "#c7ccdd", marginBottom: 20 }}>
              <strong style={{ color: "#4ade80" }}>{confirmed.credits_added} audit credits</strong>{" "}
              have been added to your account.
            </p>
            <div style={{
              background: "rgba(74,222,128,0.1)", border: "1px solid rgba(74,222,128,0.3)",
              borderRadius: 12, padding: "14px 20px", marginBottom: 28,
            }}>
              <span style={{ color: "#c7ccdd", fontSize: 14 }}>Total credits available: </span>
              <strong style={{ color: "#4ade80", fontSize: "1.4rem" }}>
                {confirmed.total_credits}
              </strong>
            </div>
            <button
              className="btn-primary"
              style={{ width: "100%", fontSize: "1rem" }}
              onClick={onSuccess}
            >
              Start My Audit →
            </button>
          </div>
        </div>
      )}

      {/* Page body */}
      <div className="payment-page" style={{ flex: 1 }}>
        <div className="payment-card">

          {/* Existing credits banner */}
          {(credits > 0 || isTest) && !confirmed && (
            <div style={{
              background: "rgba(74,222,128,0.08)",
              border: "1px solid rgba(74,222,128,0.25)",
              borderRadius: 12, padding: "14px 18px", marginBottom: 20,
              display: "flex", alignItems: "center",
              justifyContent: "space-between", gap: 12, flexWrap: "wrap",
            }}>
              <div>
                <div style={{ color: "#4ade80", fontWeight: 700, fontSize: 15 }}>
                  {isTest ? "Unlimited credits (test account)" : `You have ${credits} credit${credits !== 1 ? "s" : ""}`}
                </div>
                <div style={{ color: "#a0a8c2", fontSize: 13, marginTop: 2 }}>
                  {isTest
                    ? "No payment needed — go run an audit"
                    : `You can run ${credits} more audit${credits !== 1 ? "s" : ""} right now`}
                </div>
              </div>
              <a href="/app" className="btn-primary" style={{ padding: "9px 18px", fontSize: 14, whiteSpace: "nowrap" }}>
                Run Audit →
              </a>
            </div>
          )}

          <div className="payment-badge">AI Digital Audit Credits</div>
          <h2 className="payment-title">
            {credits > 0
              ? "Top Up Your Credits"
              : `Get ${credits_per_purchase} Audit Credits for ${formatted}`}
          </h2>
          <p className="payment-sub">
            Each credit runs one complete AI-powered digital health audit.
            Credits carry over — buy more anytime.
          </p>

          <div className="payment-price-block">
            <div className="payment-price">
              <span className="payment-currency">₹</span>
              <span className="payment-amount">{price_inr}</span>
            </div>
            <div className="payment-price-label">
              one-time · {credits_per_purchase} audit credits included
            </div>
          </div>

          <div className="payment-includes">
            <p className="payment-includes-title">WHAT YOU GET</p>
            {[
              `${credits_per_purchase} AI-powered digital presence audits`,
              "Website quality & performance score",
              "SEO health analysis",
              "Social media presence check",
              "Google Business Profile review",
              "Online reputation score",
              "Actionable recommendations PDF",
              "Credits never expire — use anytime",
            ].map((item, i) => (
              <div key={i} className="payment-include-item">
                <span>✓</span>
                <span>{item}</span>
              </div>
            ))}
          </div>

          {error && <p className="auth-error" style={{ marginBottom: 12 }}>{error}</p>}

          <button
            className="btn-primary payment-btn"
            onClick={handleBuy}
            disabled={paying}
          >
            {paying
              ? "Opening payment..."
              : credits > 0
                ? `Buy ${credits_per_purchase} More Credits — ${formatted}`
                : `Pay ${formatted} via UPI / Card`}
          </button>

          <p className="payment-secure">Secured by Razorpay · UPI, Cards, Net Banking accepted</p>
        </div>
      </div>

    </div>
  )
}
