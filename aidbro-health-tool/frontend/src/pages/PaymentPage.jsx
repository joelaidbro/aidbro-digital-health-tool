import { useState, useEffect } from "react"
import { useAuth } from "../context/AuthContext"

import { API } from "../config/api"

export default function PaymentPage({ onSuccess }) {
  const { user, authFetch, markPaid } = useAuth()
  const [status, setStatus]    = useState(null)   // payment status from backend
  const [loading, setLoading]  = useState(true)
  const [paying, setPaying]    = useState(false)
  const [error, setError]      = useState("")

  // ── Fetch current payment status ─────────────────────────────────────────
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res  = await authFetch(`${API}/payment/status`)
        const data = await res.json()
        setStatus(data)
      } catch {
        setError("Could not load payment info. Please refresh.")
      } finally {
        setLoading(false)
      }
    }
    fetchStatus()
  }, [authFetch])

  // ── Razorpay checkout ─────────────────────────────────────────────────────
  const handlePay = async () => {
    setError("")
    setPaying(true)

    try {
      const activeSearchId = sessionStorage.getItem("aidbro_active_search_id")

      // 1. Create order on backend
      const orderRes  = await authFetch(`${API}/payment/create-order`, {
        method: "POST",
        body:   JSON.stringify({
          plan_type: "basic_audit",
          search_id: activeSearchId ? Number(activeSearchId) : null,
        }),
      })
      const orderData = await orderRes.json()
      if (!orderRes.ok) throw new Error(orderData.detail || "Could not create order")

      // 2. Load Razorpay script if not already loaded
      if (!window.Razorpay) {
        await new Promise((resolve, reject) => {
          const s = document.createElement("script")
          s.src   = "https://checkout.razorpay.com/v1/checkout.js"
          s.onload  = resolve
          s.onerror = reject
          document.head.appendChild(s)
        })
      }

      // 3. Open Razorpay checkout modal
      const rzp = new window.Razorpay({
        key:         orderData.key_id,
        amount:      orderData.amount,
        currency:    orderData.currency,
        name:        orderData.business_name,
        description: orderData.description,
        order_id:    orderData.order_id,
        prefill: {
          email: orderData.prefill_email,
          name:  user?.name || "",
        },
        theme: { color: "#FF6B00" },
        modal: {
          ondismiss: () => setPaying(false),
        },
        handler: async (response) => {
          // 4. Verify payment on backend
          try {
            const verifyRes = await authFetch(`${API}/payment/verify`, {
              method: "POST",
              body:   JSON.stringify({
                razorpay_order_id:   response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature:  response.razorpay_signature,
              }),
            })
            const verifyData = await verifyRes.json()
            if (!verifyRes.ok) throw new Error(verifyData.detail || "Verification failed")

            markPaid()
            onSuccess?.()
          } catch (err) {
            setError(err.message || "Payment verification failed")
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

  if (loading) {
    return (
      <div className="payment-page">
        <div className="loading-orb" style={{ margin: "80px auto" }} />
      </div>
    )
  }

  if (status?.has_paid) {
    return (
      <div className="payment-page">
        <div className="payment-card">
          <div className="payment-success-icon">✅</div>
          <h2>You've already paid!</h2>
          <p>Your Detailed Audit is active. Head to your portal to track progress.</p>
          <button className="btn-primary" onClick={onSuccess} style={{ marginTop: 16 }}>
            Go to My Portal →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="payment-page">
      <div className="payment-card">

        {/* Header */}
        <div className="payment-badge">Stage 4 — Detailed Audit</div>
        <h2 className="payment-title">
          Unlock Your Full Digital Health Report
        </h2>
        <p className="payment-sub">
          One-time payment. Human-verified data + AI synthesis.
          Report delivered in 24–48 hours.
        </p>

        {/* Price */}
        <div className="payment-price-block">
          <div className="payment-price">
            <span className="payment-currency">₹</span>
            <span className="payment-amount">{status?.price_inr?.toLocaleString() || "—"}</span>
          </div>
          <div className="payment-price-label">one-time · 90 days portal access</div>
        </div>

        {/* What's included */}
        <div className="payment-includes">
          <p className="payment-includes-title">WHAT'S INCLUDED</p>
          {[
            ["🔍", "Full website SEO crawl — every page audited"],
            ["🏆", "Deep competitor analysis — 5 competitors"],
            ["📊", "Keyword ranking analysis (real data)"],
            ["📱", "Social media manual audit by our team"],
            ["✅", "Human-verified data with corrections"],
            ["🤖", "AI-synthesized 15–20 page report"],
            ["📞", "Follow-up consultation with Aidbro team"],
          ].map(([icon, text], i) => (
            <div key={i} className="payment-include-item">
              <span>{icon}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>

        {error && <p className="auth-error" style={{ marginBottom: 12 }}>{error}</p>}

        <button
          className="btn-primary payment-btn"
          onClick={handlePay}
          disabled={paying}
        >
          {paying ? "Opening payment..." : `Pay ₹${status?.price_inr?.toLocaleString() || "—"} via UPI / Card`}
        </button>

        <p className="payment-secure">
          🔒 Secured by Razorpay · UPI, Cards, Net Banking accepted
        </p>
      </div>
    </div>
  )
}
