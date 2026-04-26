import { useEffect, useMemo, useState } from "react"
import { useAuth } from "../context/AuthContext"
import { API } from "../config/api"

export default function PaymentPage({ onSuccess }) {
  const { user, authFetch, markPaid } = useAuth()
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [paying, setPaying] = useState(false)
  const [error, setError] = useState("")

  const activeSearchId = useMemo(() => {
    const raw = sessionStorage.getItem("aidbro_active_search_id")
    return raw ? Number(raw) : null
  }, [])

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const suffix = activeSearchId ? `?search_id=${activeSearchId}` : ""
        const res = await authFetch(`${API}/payment/status${suffix}`)
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || "Could not load payment info.")
        }
        setStatus(data)
      } catch (err) {
        setError(err.message || "Could not load payment info. Please refresh.")
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [activeSearchId, authFetch])

  const handlePay = async () => {
    setError("")
    setPaying(true)

    try {
      const orderRes = await authFetch(`${API}/payment/create-order`, {
        method: "POST",
        body: JSON.stringify({
          plan_type: "basic_audit",
          search_id: activeSearchId,
        }),
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
        name: orderData.business_name,
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
            const verifyRes = await authFetch(`${API}/payment/verify`, {
              method: "POST",
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            })
            const verifyData = await verifyRes.json()
            if (!verifyRes.ok) {
              throw new Error(verifyData.detail || "Verification failed.")
            }

            markPaid()
            onSuccess?.()
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
          <div className="payment-success-icon">OK</div>
          <h2>This search already has a paid detailed audit.</h2>
          <p>Open your portal history to track the progress of that purchased audit.</p>
          <button className="btn-primary" onClick={onSuccess} style={{ marginTop: 16 }}>
            Go to My Portal
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="payment-page">
      <div className="payment-card">
        <div className="payment-badge">Stage 4 - Detailed Audit</div>
        <h2 className="payment-title">Unlock Your Full Digital Health Report</h2>
        <p className="payment-sub">
          One-time payment. Human-verified data + AI synthesis.
          Report delivered in 24 to 48 hours.
        </p>

        <div className="payment-price-block">
          <div className="payment-price">
            <span className="payment-currency">Rs</span>
            <span className="payment-amount">{status?.price_inr?.toLocaleString() || "-"}</span>
          </div>
          <div className="payment-price-label">one-time | 90 days portal access</div>
        </div>

        {status?.account_has_paid && (
          <div className="demo-banner" style={{ marginBottom: 16, borderRadius: 12 }}>
            This account already has paid audit history. You are now purchasing a new detailed audit for the selected saved search.
          </div>
        )}

        <div className="payment-includes">
          <p className="payment-includes-title">WHAT'S INCLUDED</p>
          {[
            ["1.", "Full website SEO crawl - every page audited"],
            ["2.", "Deep competitor analysis - 5 competitors"],
            ["3.", "Keyword ranking analysis (real data)"],
            ["4.", "Social media manual audit by our team"],
            ["5.", "Human-verified data with corrections"],
            ["6.", "AI-synthesized 15 to 20 page report"],
            ["7.", "Follow-up consultation with Aidbro team"],
          ].map(([icon, text], index) => (
            <div key={index} className="payment-include-item">
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
          {paying ? "Opening payment..." : `Pay Rs ${status?.price_inr?.toLocaleString() || "-"} via UPI / Card`}
        </button>

        <p className="payment-secure">Secured by Razorpay | UPI, Cards, Net Banking accepted</p>
      </div>
    </div>
  )
}
