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
import LogSearch            from "./pages/LogSearch";
import Rules                from "./pages/Rules";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selected, setSelected] = useState(null);
  const [authPage, setAuthPage] = useState("login"); // "login" | "signup"
  const [auth, setAuth] = useState({ token: null, user: null, checked: false });

  // Restore session from localStorage on page load so a browser refresh
  // keeps the user logged in instead of bouncing back to the login screen.
  useEffect(() => {
    try {
      const token = localStorage.getItem("ww_token");
      const user  = JSON.parse(localStorage.getItem("ww_user") || "null");
      if (token && user) {
        setAuth({ token, user, checked: true });
        return;
      }
    } catch {
      // corrupt storage — fall through to logged-out state
    }
    setAuth(a => ({ ...a, checked: true }));
  }, []);

  const handleAuth = (token, user) => {
    try {
      localStorage.setItem("ww_token", token);
      localStorage.setItem("ww_user", JSON.stringify(user));
    } catch { /* storage unavailable — session will be memory-only */ }
    setAuth({ token, user, checked: true });
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem("ww_token");
      localStorage.removeItem("ww_user");
    } catch { /* ignore */ }
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
      case "alert_detail":   return <AlertDetail alertId={selected} setPage={setPage} setSelected={setSelected} />;
      case "incidents":      return <Incidents setPage={setPage} setSelected={setSelected} />;
      case "incident_detail":return <IncidentDetail incidentId={selected} setPage={setPage} />;
      case "sources":        return <LogSources />;
      case "logs":           return <LiveLogs />;
      case "reports":        return <LogSearch />;
      case "rules":          return <Rules />;
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
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--ww-card)", position: "relative" }}>
          {renderPage()}
        </div>
      </div>
    </>
  );
}
