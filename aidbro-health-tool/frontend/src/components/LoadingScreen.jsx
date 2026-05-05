import { useState, useEffect } from "react"
import loadingVideo from "../../loading_screen.mp4"

const STEPS = [
  "Searching Google Business Profile...",
  "Checking website performance...",
  "Scanning social media presence...",
  "Analyzing competitor landscape...",
  "Calculating your Digital Health Score...",
  "Generating AI-powered insights...",
]

export default function LoadingScreen() {
  const [stepIndex, setStepIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((i) => (i + 1) % STEPS.length)
    }, 1400)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="loading-screen">
      <video
        className="loading-video"
        src={loadingVideo}
        autoPlay
        loop
        muted
        playsInline
      />
      <div className="loading-steps">
        <h3>Auditing Your Business</h3>
        <div style={{ height: 28, overflow: "hidden" }}>
          {STEPS.map((step, i) => (
            <p
              key={step}
              className={`loading-step ${i === stepIndex ? "active" : ""}`}
              style={{ display: i === stepIndex ? "block" : "none" }}
            >
              {step}
            </p>
          ))}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        {STEPS.map((_, i) => (
          <div
            key={i}
            style={{
              width: i === stepIndex ? 24 : 8,
              height: 8,
              borderRadius: 4,
              background: i === stepIndex ? "var(--orange)" : "var(--border-dim)",
              transition: "all 0.4s ease",
            }}
          />
        ))}
      </div>
    </div>
  )
}
