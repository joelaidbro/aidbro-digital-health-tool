import { useState, useEffect } from "react"

const API = "http://localhost:8000/api"

// Cache price in memory to avoid repeated fetches
let cachedPrice = null

/**
 * Fetches the actual audit price from the backend .env
 * Falls back to ₹2,000 if the backend is unreachable.
 */
export function useAuditPrice() {
  const [price, setPrice]   = useState(cachedPrice || 2000)
  const [loading, setLoading] = useState(!cachedPrice)

  useEffect(() => {
    if (cachedPrice) return

    const fetchPrice = async () => {
      try {
        const res  = await fetch(`${API}/payment/status`, {
          headers: { "Authorization": "Bearer none" }  // unauthenticated — returns price_inr
        })
        if (res.ok) {
          const data = await res.json()
          if (data.price_inr) {
            cachedPrice = data.price_inr
            setPrice(data.price_inr)
          }
        }
      } catch {
        // Backend unreachable — use default
      } finally {
        setLoading(false)
      }
    }

    fetchPrice()
  }, [])

  return { price, loading, formatted: `₹${price.toLocaleString("en-IN")}` }
}
