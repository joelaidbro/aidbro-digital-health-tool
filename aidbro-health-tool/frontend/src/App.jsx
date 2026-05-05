import { useState } from "react"
import { AuthProvider, useAuth } from "./context/AuthContext"
import SearchForm from "./components/SearchForm"
import ResultsDashboard from "./components/ResultsDashboard"
import LoadingScreen from "./components/LoadingScreen"
import AuthPage from "./pages/AuthPage"
import AuthCallbackPage from "./pages/AuthCallbackPage"
import PaymentPage from "./pages/PaymentPage"
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

function InnerApp() {
  const { isAuthenticated, loading } = useAuth()
  const path = window.location.pathname.replace(/\/+$/, "") || "/"

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
          const next = result === "success" ? "/portal" : "/auth"
          window.history.replaceState({}, "", next)
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
      window.history.replaceState({}, "", "/portal")
      window.location.reload()
      return null
    }

    return (
      <PublicShell>
        <AuthPage
          initialMode={path === "/register" ? "register" : "login"}
          onSuccess={() => {
            window.history.replaceState({}, "", "/portal")
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
      <PublicShell>
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
      <PublicShell>
        <ClientPortal
          onLogout={() => {
            window.history.replaceState({}, "", "/")
            window.location.reload()
          }}
        />
      </PublicShell>
    )
  }

  return <FreeAuditApp />
}

function FreeAuditApp() {
  const { token, isAuthenticated } = useAuth()
  const [state, setState] = useState("idle")
  const [results, setResults] = useState(null)
  const [leadId, setLeadId] = useState(null)
  const [searchId, setSearchId] = useState(null)
  const [error, setError] = useState("")
  const [limitBlocked, setLimitBlocked] = useState(false)

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
    setLimitBlocked(false)

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
        setLimitBlocked(res.status === 429)
        throw new Error(data.detail || "Audit failed. Please try again.")
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
    setLimitBlocked(false)
  }

  return (
    <>
      {state === "idle" && (
        <PublicShell>
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
        <PublicShell>
          <div className="error-screen">
            <div className="error-card">
              <span className="error-icon">!</span>
              <h2>Something went wrong</h2>
              <p>{error}</p>
              {limitBlocked && !isAuthenticated && (
                <a href="/auth" className="btn-primary" style={{ marginBottom: 12 }}>
                  Login to Continue
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
