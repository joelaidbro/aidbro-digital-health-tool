import logo from "../../aidbroai-logo.png"

export default function SiteLogo({ badge = "", compact = false }) {
  return (
    <div className={`site-logo ${compact ? "compact" : ""}`}>
      <img src={logo} alt="Aidbro AI" className="site-logo-image" />
      {badge && <span className="navbar-badge">{badge}</span>}
    </div>
  )
}
