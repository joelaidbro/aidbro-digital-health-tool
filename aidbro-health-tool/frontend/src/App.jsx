import { useState } from "react"
import { AuthProvider, useAuth } from "./context/AuthContext"
import SearchForm from "./components/SearchForm"
import ResultsDashboard from "./components/ResultsDashboard"
import LoadingScreen from "./components/LoadingScreen"
import AuthPage from "./pages/AuthPage"
import AuthCallbackPage from "./pages/AuthCallbackPage"
import PaymentPage from "./pages/PaymentPage"
import BuyCreditsPage from "./pages/BuyCreditsPage"
import ClientPortal from "./pages/ClientPortal"
import InfoPage from "./pages/InfoPage"
import SiteFooter from "./components/SiteFooter"
import FloatingWhatsApp from "./components/FloatingWhatsApp"
import { SITE_PAGES } from "./content/siteContent"
import { API } from "./config/api"

function PublicShell({
  children,
  showFooter = true,
  showWhatsApp = true,
  showPattern = true,
}) {
  return (
    <div
      className="app-root"
      style={showPattern ? undefined : { background: "#030714" }}
    >
      {showPattern && <div className="bg-grid" />}
      {showPattern && <div className="bg-glow" />}
      {children}
      {showFooter && <SiteFooter />}
      {showWhatsApp && <FloatingWhatsApp />}
    </div>
  )
}

function NoCreditsScreen() {
  return (
    <PublicShell showFooter={false}>
      <div className="error-screen">
        <div className="error-card">
          <span className="error-icon" style={{ fontSize: "2rem" }}>🎟️</span>
          <h2>No Audit Credits</h2>
          <p>
            You've used all your audit credits. Purchase more to continue
            running digital health audits.
          </p>
          <a href="/buy-credits" className="btn-primary" style={{ marginBottom: 12 }}>
            Buy 2 Credits — ₹299
          </a>
          <a href="/portal" className="btn-secondary" style={{ display: "block", textAlign: "center" }}>
            View Past Audits
          </a>
        </div>
      </div>
    </PublicShell>
  )
}

function InnerApp() {
  const { isAuthenticated, loading, user } = useAuth()
  const path = window.location.pathname.replace(/\/+$/, "") || "/"
  const searchParams = new URLSearchParams(window.location.search)
  const intent = searchParams.get("intent")

  if (loading) {
    return (
      <PublicShell showFooter={false} showWhatsApp={false} showPattern={false}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
          }}
        >
          <div className="loading-orb" />
        </div>
      </PublicShell>
    )
  }

  if (path === "/auth/callback") {
    return (
      <AuthCallbackPage
        onComplete={(result) => {
          if (result === "success") {
            const savedIntent = sessionStorage.getItem("aidbro_auth_intent")
            sessionStorage.removeItem("aidbro_auth_intent")
            const next = savedIntent === "buy-credits" ? "/buy-credits" : "/app"
            window.history.replaceState({}, "", next)
          } else {
            window.history.replaceState({}, "", "/auth")
          }
          window.location.reload()
        }}
      />
    )
  }

  if (SITE_PAGES[path]) {
    return (
      <PublicShell showFooter={false}>
        <InfoPage page={SITE_PAGES[path]} />
      </PublicShell>
    )
  }

  if (path === "/auth" || path === "/login" || path === "/register") {
    if (isAuthenticated) {
      const next = intent === "buy-credits" ? "/buy-credits" : "/app"
      window.history.replaceState({}, "", next)
      window.location.reload()
      return null
    }
    // Persist intent across OAuth redirect
    if (intent) {
      sessionStorage.setItem("aidbro_auth_intent", intent)
    }
    return (
      <PublicShell showFooter={false}>
        <AuthPage
          initialMode={path === "/register" ? "register" : "login"}
          intent={intent}
          onSuccess={() => {
            const savedIntent = sessionStorage.getItem("aidbro_auth_intent") || intent
            sessionStorage.removeItem("aidbro_auth_intent")
            const next = savedIntent === "buy-credits" ? "/buy-credits" : "/app"
            window.history.replaceState({}, "", next)
            window.location.reload()
          }}
        />
      </PublicShell>
    )
  }

  if (path === "/buy-credits") {
    if (!isAuthenticated) {
      window.history.replaceState({}, "", "/auth?intent=buy-credits")
      window.location.reload()
      return null
    }
    return (
      <PublicShell showFooter={false}>
        <BuyCreditsPage
          onSuccess={() => {
            window.history.replaceState({}, "", "/app")
            window.location.reload()
          }}
        />
      </PublicShell>
    )
  }

  if (path === "/upgrade") {
    if (!isAuthenticated) {
      window.history.replaceState({}, "", "/auth")
      window.location.reload()
      return null
    }
    return (
      <PublicShell showFooter={false}>
        <PaymentPage
          onSuccess={() => {
            window.history.replaceState({}, "", "/portal")
            window.location.reload()
          }}
        />
      </PublicShell>
    )
  }

  if (path === "/portal") {
    if (!isAuthenticated) {
      window.history.replaceState({}, "", "/auth")
      window.location.reload()
      return null
    }
    return (
      <PublicShell showFooter={false} showWhatsApp={false}>
        <ClientPortal
          onLogout={() => {
            window.history.replaceState({}, "", "/")
            window.location.reload()
          }}
        />
      </PublicShell>
    )
  }

  if (path === "/app") {
    if (!isAuthenticated) {
      window.history.replaceState({}, "", "/auth")
      window.location.reload()
      return null
    }
    const credits = user?.audit_credits ?? 0
    const isTest  = user?.is_test_account ?? false
    if (!isTest && credits <= 0) {
      return <NoCreditsScreen />
    }
    return <FreeAuditApp />
  }

  // Any other path: redirect to landing
  window.location.href = "/"
  return null
}

function CreditBadge() {
  const { user } = useAuth()
  const credits = user?.audit_credits ?? 0
  const isTest  = user?.is_test_account ?? false
  const low     = !isTest && credits <= 1

  return (
    <div style={{ textAlign: "center", paddingTop: 16, paddingBottom: 4 }}>
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          background: "rgba(255,255,255,0.07)",
          border: `1px solid ${low ? "rgba(248,113,113,0.4)" : "rgba(255,255,255,0.14)"}`,
          borderRadius: 999,
          padding: "6px 18px",
          color: "#c7ccdd",
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        Audit Credits:&nbsp;
        <strong style={{ color: isTest ? "#a78bfa" : low ? "#f87171" : "#4ade80" }}>
          {isTest ? "Unlimited" : credits}
        </strong>
        {!isTest && low && (
          <a
            href="/buy-credits"
            style={{ color: "#ff7a00", fontWeight: 700, marginLeft: 4 }}
          >
            Buy More
          </a>
        )}
      </span>
    </div>
  )
}

function FreeAuditApp() {
  const { token, user, updateCredits } = useAuth()
  const [state, setState] = useState("idle")
  const [results, setResults] = useState(null)
  const [leadId, setLeadId] = useState(null)
  const [searchId, setSearchId] = useState(null)
  const [error, setError] = useState("")
  const [noCredits, setNoCredits] = useState(false)

  const handleSearch = async ({
    businessName,
    location,
    category,
    mobileNumber,
    websiteUrl,
    instagramUrl,
    facebookUrl,
    linkedinUrl,
  }) => {
    setState("loading")
    setError("")
    setNoCredits(false)

    try {
      const res = await fetch(`${API}/audit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          business_name: businessName,
          location,
          category,
          mobile_number: mobileNumber || "",
          website_url: websiteUrl || "",
          instagram_url: instagramUrl || "",
          facebook_url: facebookUrl || "",
          linkedin_url: linkedinUrl || "",
        }),
      })

      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        if (res.status === 403) {
          setNoCredits(true)
        }
        throw new Error(data.detail || "Audit failed. Please try again.")
      }

      // Decrement credit count locally on successful audit
      if (!user?.is_test_account) {
        updateCredits(Math.max(0, (user?.audit_credits ?? 1) - 1))
      }

      setLeadId(data.lead_id || null)
      setSearchId(data.search_id || null)
      if (data.search_id) {
        sessionStorage.setItem("aidbro_active_search_id", String(data.search_id))
      }
      setResults(data)
      setState("results")
    } catch (e) {
      setError(e.message || "Something went wrong.")
      setState("error")
    }
  }

  const handleReset = () => {
    sessionStorage.removeItem("aidbro_active_search_id")
    setState("idle")
    setResults(null)
    setLeadId(null)
    setSearchId(null)
    setError("")
    setNoCredits(false)
  }

  return (
    <>
      {state === "idle" && (
        <PublicShell>
          <CreditBadge />
          <SearchForm onSearch={handleSearch} />
        </PublicShell>
      )}
      {state === "loading" && (
        <PublicShell showFooter={false} showWhatsApp={false} showPattern={false}>
          <LoadingScreen />
        </PublicShell>
      )}
      {state === "results" && results && (
        <PublicShell showFooter={false}>
          <ResultsDashboard data={results} leadId={leadId} searchId={searchId} onReset={handleReset} />
        </PublicShell>
      )}
      {state === "error" && (
        <PublicShell showFooter={false}>
          <div className="error-screen">
            <div className="error-card">
              <span className="error-icon">!</span>
              <h2>Something went wrong</h2>
              <p>{error}</p>
              {noCredits && (
                <a href="/buy-credits" className="btn-primary" style={{ marginBottom: 12 }}>
                  Buy Credits — ₹299
                </a>
              )}
              <button className="btn-primary" onClick={handleReset}>Try Again</button>
            </div>
          </div>
        </PublicShell>
      )}
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <InnerApp />
    </AuthProvider>
  )
}
