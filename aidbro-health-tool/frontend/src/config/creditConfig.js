import { useState, useEffect } from "react"
import { API } from "./api"

// Cache in memory so only one network request per page load
let cached = null

const DEFAULTS = { price_inr: 299, credits_per_purchase: 2 }

/**
 * Fetches credit purchase config from the backend (single source of truth).
 * Falls back to defaults if the backend is unreachable.
 */
export function useCreditConfig() {
  const [config, setConfig] = useState(cached || DEFAULTS)
  const [loading, setLoading] = useState(!cached)

  useEffect(() => {
    if (cached) return
    fetch(`${API}/payment/credits/info`)
      .then((r) => r.json())
      .then((data) => {
        if (data.price_inr) {
          cached = {
            price_inr:            data.price_inr,
            credits_per_purchase: data.credits_per_purchase ?? DEFAULTS.credits_per_purchase,
          }
          setConfig(cached)
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return {
    ...config,
    loading,
    formatted: `₹${config.price_inr.toLocaleString("en-IN")}`,
  }
}
