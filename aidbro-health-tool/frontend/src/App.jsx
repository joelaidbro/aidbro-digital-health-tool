import { useState } from "react"
import SearchForm from "./components/SearchForm"
import ResultsDashboard from "./components/ResultsDashboard"
import LoadingScreen from "./components/LoadingScreen"

export default function App() {
  const [state, setState]     = useState("idle")
  const [results, setResults] = useState(null)
  const [error, setError]     = useState("")

  const handleSearch = async ({
    businessName,
    location,
    category,
    websiteUrl,
    instagramUrl,
    facebookUrl,
    linkedinUrl,
  }) => {
    setState("loading")
    setError("")
    try {
      const res = await fetch("http://localhost:8000/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name:  businessName,
          location:       location,
          category:       category,
          website_url:    websiteUrl    || "",
          instagram_url:  instagramUrl  || "",
          facebook_url:   facebookUrl   || "",
          linkedin_url:   linkedinUrl   || "",
        }),
      })
      if (!res.ok) throw new Error("Audit failed. Please try again.")
      const data = await res.json()
      setResults(data)
      setState("results")
    } catch (e) {
      setError(e.message || "Something went wrong.")
      setState("error")
    }
  }

  const handleReset = () => {
    setState("idle")
    setResults(null)
    setError("")
  }

  return (
    <div className="app-root">
      <div className="bg-grid" />
      <div className="bg-glow" />

      {state === "idle"    && <SearchForm onSearch={handleSearch} />}
      {state === "loading" && <LoadingScreen />}
      {state === "results" && results && (
        <ResultsDashboard data={results} onReset={handleReset} />
      )}
      {state === "error" && (
        <div className="error-screen">
          <div className="error-card">
            <span className="error-icon">⚠️</span>
            <h2>Something went wrong</h2>
            <p>{error}</p>
            <button className="btn-primary" onClick={handleReset}>
              ← Try Again
            </button>
          </div>
        </div>
      )}
    </div>
  )
}