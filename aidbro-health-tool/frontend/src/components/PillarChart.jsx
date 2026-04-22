import { useEffect, useState } from "react"

const COLOR_MAP = {
  green:  "var(--green)",
  yellow: "var(--yellow)",
  red:    "var(--red)",
}

export default function PillarChart({ pillars }) {
  const [animated, setAnimated] = useState(false)
  const entries = Object.values(pillars || {})

  // Trigger animation after mount — this is the fix for the chart not animating
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(t)
  }, [])

  if (!entries.length) return null

  return (
    <div className="pillar-chart-v2">
      <div className="pillar-chart-title">Pillar Breakdown</div>
      <div className="pillar-chart-bars">
        {entries.map((p, i) => {
          const pct   = p.percent || 0
          const color = COLOR_MAP[p.color] || "var(--gray)"
          return (
            <div key={i} className="pillar-chart-bar-col">
              {/* Value label at top */}
              <div className="pillar-chart-val" style={{ color }}>
                {p.score}/{p.max}
              </div>

              {/* Bar track */}
              <div className="pillar-chart-track">
                <div
                  className="pillar-chart-fill"
                  style={{
                    height:     animated ? `${pct}%` : "0%",
                    background: color,
                    boxShadow:  animated ? `0 0 12px ${color}44` : "none",
                    transition: `height 1.2s cubic-bezier(0.34,1.56,0.64,1) ${i*0.1}s,
                                 box-shadow 0.6s ease ${i*0.1}s`,
                  }}
                />
                {/* Percentage label inside bar */}
                <div
                  className="pillar-chart-pct-inside"
                  style={{ opacity: animated ? 1 : 0, transition: `opacity 0.5s ease ${i*0.1+0.6}s` }}
                >
                  {pct}%
                </div>
              </div>

              {/* Icon + name */}
              <div className="pillar-chart-icon">{p.icon}</div>
              <div className="pillar-chart-name">{p.name.split(" ")[0]}</div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="pillar-chart-legend">
        {[
          { color: "var(--green)",  label: "Strong (≥75%)" },
          { color: "var(--yellow)", label: "Average (50–74%)" },
          { color: "var(--red)",    label: "Weak (<50%)" },
        ].map((l, i) => (
          <div key={i} className="pillar-chart-legend-item">
            <span className="kw-dot" style={{ background: l.color }} />
            {l.label}
          </div>
        ))}
      </div>
    </div>
  )
}
