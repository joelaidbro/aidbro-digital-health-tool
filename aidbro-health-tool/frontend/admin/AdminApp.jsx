import { useCallback, useEffect, useState } from "react"
import AdminLogin from "./pages/AdminLogin"
import AnonymousSearches from "./pages/AnonymousSearches"
import AnonymousSearchDetail from "./pages/AnonymousSearchDetail"
import LeadsTable from "./pages/LeadsTable"
import LeadDetail from "./pages/LeadDetail"
import UsersTable from "./pages/UsersTable"
import UserDetail from "./pages/UserDetail"
import AuditQueue from "./pages/AuditQueue"
import AuditEditor from "./pages/AuditEditor"
import Analytics from "./pages/Analytics"
import TeamManagement from "./pages/TeamManagement"
import { API } from "../src/config/api"
const TOKEN_KEY = "aidbro_admin_token"
const USER_KEY = "aidbro_admin_user"

export default function AdminApp() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || "")
  const [user, setUser] = useState(() => {
    const stored = sessionStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  })
  const [checkingSession, setCheckingSession] = useState(true)
  const [loginError, setLoginError] = useState("")
  const [loginLoading, setLoginLoading] = useState(false)
  const [activePage, setActivePage] = useState("dashboard")
  const [selectedAnonymousSearchId, setSelectedAnonymousSearchId] = useState(null)
  const [selectedLeadId, setSelectedLeadId] = useState(null)
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [selectedAuditId, setSelectedAuditId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleLogout = useCallback(() => {
    setToken("")
    setUser(null)
    setSelectedAnonymousSearchId(null)
    setSelectedLeadId(null)
    setSelectedUserId(null)
    setSelectedAuditId(null)
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)
  }, [])

  useEffect(() => {
    if (!token) {
      setCheckingSession(false)
      return
    }

    let cancelled = false

    const restoreSession = async () => {
      try {
        const res = await fetch(`${API}/auth/me`, {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        })

        if (!res.ok) {
          throw new Error("Session expired")
        }

        const data = await res.json()
        if (!cancelled) {
          setUser(data)
        }
      } catch {
        if (!cancelled) {
          handleLogout()
        }
      } finally {
        if (!cancelled) {
          setCheckingSession(false)
        }
      }
    }

    restoreSession()

    return () => {
      cancelled = true
    }
  }, [token, handleLogout])

  const storeSession = (nextToken, nextUser) => {
    setToken(nextToken)
    setUser(nextUser)
    sessionStorage.setItem(TOKEN_KEY, nextToken)
    sessionStorage.setItem(USER_KEY, JSON.stringify(nextUser))
  }

  const handleLogin = async ({ email, password }) => {
    setLoginError("")
    setLoginLoading(true)
    try {
      const res = await fetch(`${API}/auth/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || "Login failed")
      }
      storeSession(data.access_token, data.user)
    } catch (error) {
      setLoginError(error.message || "Could not sign in")
    } finally {
      setLoginLoading(false)
      setCheckingSession(false)
    }
  }

  const bumpRefresh = () => setRefreshKey((value) => value + 1)

  const pageTitle = {
    dashboard: "Operations Dashboard",
    anonymous: "Anonymous Search Intake",
    users: "Registered Users",
    leads: "Legacy Leads CRM",
    audits: "Detailed Audit Queue",
    team: "Team Management",
  }[activePage]

  const sidebarItems = [
    { key: "dashboard", label: "Overview", icon: "OV" },
    { key: "anonymous", label: "Anonymous Searches", icon: "AN" },
    { key: "users", label: "Registered Users", icon: "US" },
    { key: "leads", label: "Legacy Leads", icon: "LD" },
    { key: "audits", label: "Audit Queue", icon: "AQ" },
  ]

  if (user?.role === "super_admin") {
    sidebarItems.push({ key: "team", label: "Team", icon: "TM" })
  }

  if (checkingSession) {
    return (
      <div className="app-root">
        <div className="bg-grid" />
        <div className="bg-glow" />
        <div className="admin-loading-shell">
          <div className="loading-orb" />
          <p>Loading admin workspace...</p>
        </div>
      </div>
    )
  }

  if (!token || !user) {
    return (
      <div className="app-root">
        <div className="bg-grid" />
        <div className="bg-glow" />
        <AdminLogin
          loading={loginLoading}
          error={loginError}
          onLogin={handleLogin}
        />
      </div>
    )
  }

  return (
    <div className="admin-shell">
      <div className="bg-grid" />
      <div className="bg-glow" />

      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-title">
            Aidbro <span>Admin</span>
          </div>
          <p>Internal audit operations console</p>
        </div>

        <nav className="admin-nav">
          {sidebarItems.map((item) => (
            <button
              key={item.key}
              className={`admin-nav-item ${activePage === item.key ? "active" : ""}`}
              onClick={() => setActivePage(item.key)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-footer">
          <div className="admin-user-chip">
            <div className="admin-user-chip-name">{user.name || user.email}</div>
            <div className="admin-user-chip-role">{(user.role || "").replace("_", " ")}</div>
          </div>
          <button className="btn-ghost" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <div>
            <div className="admin-page-kicker">Aidbro Operations</div>
            <h1>{pageTitle}</h1>
          </div>
          <div className="admin-topbar-meta">
            <span className="navbar-badge">Logged in as {user.role}</span>
            <button className="btn-primary" onClick={bumpRefresh}>
              Refresh Data
            </button>
          </div>
        </header>

        {activePage === "dashboard" && (
          <Analytics token={token} refreshKey={refreshKey} onUnauthorized={handleLogout} />
        )}

        {activePage === "anonymous" && (
          <div className="admin-workspace admin-workspace-split">
            <AnonymousSearches
              token={token}
              refreshKey={refreshKey}
              selectedSearchId={selectedAnonymousSearchId}
              onSelectSearch={setSelectedAnonymousSearchId}
              onUnauthorized={handleLogout}
            />
            <AnonymousSearchDetail
              token={token}
              searchId={selectedAnonymousSearchId}
              refreshKey={refreshKey}
              onOpenAudit={(clientId) => {
                setSelectedAuditId(clientId)
                setActivePage("audits")
              }}
              onUnauthorized={handleLogout}
            />
          </div>
        )}

        {activePage === "users" && (
          <div className="admin-workspace admin-workspace-split">
            <UsersTable
              token={token}
              refreshKey={refreshKey}
              selectedUserId={selectedUserId}
              onSelectUser={setSelectedUserId}
              onUnauthorized={handleLogout}
            />
            <UserDetail
              token={token}
              userId={selectedUserId}
              refreshKey={refreshKey}
              onOpenAudit={(clientId) => {
                setSelectedAuditId(clientId)
                setActivePage("audits")
              }}
              onUnauthorized={handleLogout}
            />
          </div>
        )}

        {activePage === "leads" && (
          <div className="admin-workspace admin-workspace-split">
            <LeadsTable
              token={token}
              refreshKey={refreshKey}
              selectedLeadId={selectedLeadId}
              onSelectLead={setSelectedLeadId}
              onUnauthorized={handleLogout}
            />
            <LeadDetail
              token={token}
              leadId={selectedLeadId}
              refreshKey={refreshKey}
              onSaved={bumpRefresh}
              onOpenAudit={(clientId) => {
                setSelectedAuditId(clientId)
                setActivePage("audits")
              }}
              onUnauthorized={handleLogout}
            />
          </div>
        )}

        {activePage === "audits" && (
          <div className="admin-workspace admin-workspace-split admin-workspace-audits">
            <AuditQueue
              token={token}
              refreshKey={refreshKey}
              selectedAuditId={selectedAuditId}
              onSelectAudit={setSelectedAuditId}
              onUnauthorized={handleLogout}
            />
            <AuditEditor
              token={token}
              auditId={selectedAuditId}
              user={user}
              refreshKey={refreshKey}
              onSaved={bumpRefresh}
              onUnauthorized={handleLogout}
            />
          </div>
        )}

        {activePage === "team" && user.role === "super_admin" && (
          <TeamManagement
            token={token}
            refreshKey={refreshKey}
            onSaved={bumpRefresh}
            onUnauthorized={handleLogout}
          />
        )}
      </main>
    </div>
  )
}
