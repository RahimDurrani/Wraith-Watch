// src/App.jsx
// ─────────────────────────────────────────────────────────
// Root component — auth gating, routing, global styles.
// This is the only file that imports everything else.
// ─────────────────────────────────────────────────────────
import { useState, useEffect } from "react";

import { Sidebar }           from "./components/Sidebar";
import { Placeholder }       from "./components/UI";

import { Login, Signup }     from "./pages/Auth";
import Dashboard             from "./pages/Dashboard";
import { Alerts,
         AlertDetail }       from "./pages/Alerts";
import { Incidents,
         IncidentDetail }    from "./pages/Incidents";
import LogSources            from "./pages/LogSources";
import UploadLogs            from "./pages/UploadLogs";
import LiveLogs              from "./pages/LiveLogs";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selected, setSelected] = useState(null);
  const [authPage, setAuthPage] = useState("login"); // "login" | "signup"
  const [auth, setAuth] = useState({ token: null, user: null, checked: false });

  // Restore session from in-memory token on mount (no localStorage in this preview environment —
  // in your real React app, swap this for localStorage.getItem("ww_token"))
  useEffect(() => {
    setAuth(a => ({ ...a, checked: true }));
  }, []);

  const handleAuth = (token, user) => {
    setAuth({ token, user, checked: true });
  };

  const handleLogout = () => {
    setAuth({ token: null, user: null, checked: true });
    setPage("dashboard");
    setAuthPage("login");
  };

  if (!auth.checked) return null;

  if (!auth.token) {
    return authPage === "login"
      ? <Login onAuth={handleAuth} goSignup={() => setAuthPage("signup")} />
      : <Signup onAuth={handleAuth} goLogin={() => setAuthPage("login")} />;
  }

  const renderPage = () => {
    switch (page) {
      case "dashboard":      return <Dashboard setPage={setPage} setSelected={setSelected} />;
      case "alerts":         return <Alerts setPage={setPage} setSelected={setSelected} />;
      case "alert_detail":   return <AlertDetail alertId={selected} setPage={setPage} />;
      case "incidents":      return <Incidents setPage={setPage} setSelected={setSelected} />;
      case "incident_detail":return <IncidentDetail incidentId={selected} setPage={setPage} />;
      case "sources":        return <LogSources />;
      case "logs":           return <LiveLogs />;
      case "reports":        return <Placeholder title="Reports" icon="file-analytics" />;
      case "rules":          return <Placeholder title="Rules" icon="shield-check" />;
      case "upload":         return <UploadLogs />;
      default:               return <Dashboard setPage={setPage} setSelected={setSelected} />;
    }
  };

  return (
    <>
      <style>{`
        :root {
          --ww-text: #1A1A18;
          --ww-muted: #73726C;
          --ww-border: rgba(0,0,0,0.12);
          --ww-card: #FFFFFF;
          --ww-surface: #F5F4F0;
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --ww-text: #E8E6DF;
            --ww-muted: #9B9A94;
            --ww-border: rgba(255,255,255,0.1);
            --ww-card: #1E1E1C;
            --ww-surface: #161614;
          }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        textarea:focus, select:focus, input:focus { outline: 2px solid #378ADD; outline-offset: 1px; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.3); border-radius: 3px; }
      `}</style>
      <div style={{
        display: "flex", height: "100vh", width: "100vw",
        background: "var(--ww-surface)", overflow: "hidden",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}>
        <Sidebar page={page} setPage={setPage} user={auth.user} onLogout={handleLogout} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--ww-card)" }}>
          {renderPage()}
        </div>
      </div>
    </>
  );
}
