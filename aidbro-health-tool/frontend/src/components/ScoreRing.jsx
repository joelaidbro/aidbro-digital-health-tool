export default function ScoreRing({ score, size = 120 }) {
  const radius = size / 2 - 10
  const circumference = 2 * Math.PI * radius
  const filled = (score / 100) * circumference

  const color =
    score >= 70 ? "var(--green)" :
    score >= 50 ? "var(--yellow)" :
    "var(--red)"

  const grade =
    score >= 80 ? "A" :
    score >= 65 ? "B" :
    score >= 50 ? "C" :
    score >= 35 ? "D" : "F"

  return (
    <div className="score-hero">
      <div className="score-ring" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="var(--border-dim)" strokeWidth={8}
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circumference}`}
            style={{ transition: "stroke-dasharray 1.2s ease" }}
          />
        </svg>
        <div className="score-ring-text">
          <span className="score-ring-num" style={{ color }}>{score}</span>
          <span className="score-ring-label">/ 100</span>
        </div>
      </div>
      <div className="score-grade" style={{ color }}>{grade}</div>
      <div className="score-grade-label">
        {score >= 80 ? "Excellent" :
         score >= 65 ? "Good" :
         score >= 50 ? "Average" :
         score >= 35 ? "Needs Work" : "Critical"}
      </div>
    </div>
  )
}