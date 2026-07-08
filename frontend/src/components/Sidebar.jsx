
export function Sidebar({ page, setPage, user, onLogout }) {
  const initial = (user?.username || "A")[0].toUpperCase();

  const nav = (id, icon, label, badge, badgeColor) => (
    <div
      key={id}
      onClick={() => setPage(id)}
      style={{
        display: "flex", alignItems: "center", gap: 9,
        padding: "7px 10px", borderRadius: 8, cursor: "pointer",
        fontSize: 13, marginBottom: 2,
        background: page === id ? "var(--ww-card)"    : "transparent",
        color:      page === id ? "var(--ww-text)"    : "var(--ww-muted)",
        fontWeight: page === id ? 500                 : 400,
      }}
    >
      <i className={`ti ti-${icon}`} style={{ fontSize: 16, minWidth: 16 }} aria-hidden="true" />
      <span style={{ flex: 1 }}>{label}</span>
      {badge && (
        <span style={{
          fontSize: 10, padding: "1px 6px", borderRadius: 99,
          background: badgeColor?.bg   || "#FAECE7",
          color:      badgeColor?.text || "#712B13",
        }}>{badge}</span>
      )}
    </div>
  );

  return (
    <div style={{
      width: 210, minWidth: 210,
      background: "var(--ww-surface)",
      borderRight: "0.5px solid var(--ww-border)",
      display: "flex", flexDirection: "column",
    }}>
      {/* Logo */}
      <div style={{ padding: "16px 14px 14px", borderBottom: "0.5px solid var(--ww-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
          <i className="ti ti-eye" style={{ fontSize: 18, color: "#378ADD" }} aria-hidden="true" />
          <span style={{ fontSize: 15, fontWeight: 500, color: "var(--ww-text)" }}>WraithWatch</span>
        </div>
        <div style={{ fontSize: 10, color: "var(--ww-muted)", paddingLeft: 26 }}>DFIR SIEM Platform</div>
      </div>

      {/* Nav items */}
      <div style={{ padding: "12px 8px 0", flex: 1 }}>
        <NavSection label="Monitor">
          {nav("dashboard", "layout-dashboard", "Dashboard")}
          {nav("alerts",    "bell",              "Alerts",  14, { bg: "#FAECE7", text: "#712B13" })}
          {nav("logs",      "activity",          "Live logs")}
          {nav("sources",   "heart-rate-monitor","Log sources")}
        </NavSection>

        <NavSection label="Respond">
          {nav("incidents", "folder-open",    "Incidents", 3, { bg: "#FAEEDA", text: "#633806" })}
          {nav("reports",   "file-analytics", "Reports")}
        </NavSection>

        <NavSection label="Configure">
          {nav("rules",  "shield-check", "Rules")}
          {nav("upload", "upload",       "Upload logs")}
        </NavSection>
      </div>

      {/* User footer */}
      <div style={{ padding: "10px 8px", borderTop: "0.5px solid var(--ww-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "7px 10px" }}>
          <div style={{
            width: 26, height: 26, borderRadius: "50%",
            background: "#E6F1FB", color: "#0C447C",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 11, fontWeight: 500, flexShrink: 0,
          }}>{initial}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: "var(--ww-text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.username || "Analyst"}
            </div>
            <div style={{ fontSize: 10, color: "var(--ww-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.email || "analyst@soc.local"}
            </div>
          </div>
          <button
            onClick={onLogout}
            title="Log out"
            aria-label="Log out"
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ww-muted)", padding: 4, display: "flex" }}
          >
            <i className="ti ti-logout" style={{ fontSize: 15 }} aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}

function NavSection({ label, children }) {
  return (
    <>
      <div style={{
        fontSize: 10, color: "var(--ww-muted)", textTransform: "uppercase",
        letterSpacing: ".08em", padding: "10px 10px 4px",
      }}>{label}</div>
      {children}
    </>
  );
}
