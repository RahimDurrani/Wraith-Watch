// src/pages/Alerts.jsx
import { useState, useEffect }      from "react";
import { useFetch }                 from "../hooks/useFetch";
import { API, SEV_CONFIG,
         STATUS_CONFIG }            from "../utils/constants";
import { Badge, Card, CardTitle,
         AbuseBar, Topbar, TopBtn } from "../components/UI";

function Alerts({ setPage, setSelected }) {
  const [sevFilter, setSevFilter] = useState("");
  const [srcFilter, setSrcFilter] = useState("");
  const url = `${API}/alerts${sevFilter || srcFilter ? `?${sevFilter ? `severity=${sevFilter}` : ""}${sevFilter && srcFilter ? "&" : ""}${srcFilter ? `log_type=${srcFilter}` : ""}` : ""}`;
  const { data: alerts, reload } = useFetch(url);

  // New alerts can appear at any time from the live log generator's rule
  // engine, so keep this list current without requiring a manual refresh.
  useEffect(() => {
    const id = setInterval(reload, 8000);
    return () => clearInterval(id);
  }, [reload]);

  return (
    <>
      <Topbar title="Alerts">
        <TopBtn icon="refresh" label="Refresh" onClick={reload} />
        <select value={sevFilter} onChange={e => setSevFilter(e.target.value)} style={{ fontSize: 12, padding: "4px 8px", borderRadius: 6, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)" }}>
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={srcFilter} onChange={e => setSrcFilter(e.target.value)} style={{ fontSize: 12, padding: "4px 8px", borderRadius: 6, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)" }}>
          <option value="">All sources</option>
          <option value="apache">Apache</option>
          <option value="syslog">Syslog</option>
          <option value="evtx">EVTX</option>
        </select>
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        <div style={{ border: "0.5px solid var(--ww-border)", borderRadius: 10, overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "90px 1fr 110px 110px 90px 80px", padding: "8px 14px", background: "var(--ww-surface)", borderBottom: "0.5px solid var(--ww-border)" }}>
            {["Severity","Alert","Source IP","Source","Time","Status"].map(h => (
              <span key={h} style={{ fontSize: 10, fontWeight: 500, color: "var(--ww-muted)" }}>{h}</span>
            ))}
          </div>
          {(alerts || []).map(a => (
            <div key={a.id} onClick={() => { setSelected(a.id); setPage("alert_detail"); }}
              style={{ display: "grid", gridTemplateColumns: "90px 1fr 110px 110px 90px 80px", padding: "9px 14px", borderBottom: "0.5px solid var(--ww-border)", cursor: "pointer", background: "var(--ww-card)", alignItems: "center" }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--ww-surface)"}
              onMouseLeave={e => e.currentTarget.style.background = "var(--ww-card)"}>
              <div><Badge label={a.severity} config={SEV_CONFIG[a.severity]} /></div>
              <span style={{ fontSize: 12, color: "var(--ww-text)" }}>{a.title}</span>
              <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-muted)" }}>{a.source_ip}</span>
              <span style={{ fontSize: 11, color: "var(--ww-muted)", textTransform: "uppercase" }}>{a.log_type}</span>
              <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{new Date(a.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
              <Badge label={a.status.replace("_"," ")} config={STATUS_CONFIG[a.status]} />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function AlertDetail({ alertId, setPage, setSelected }) {
  const { data: alert } = useFetch(`${API}/alerts/${alertId}`);
  const [busy, setBusy]   = useState(null);   // "incident" | "pdf" | null
  const [error, setError] = useState(null);

  // Create (or reuse) the incident linked to this alert, and return its id.
  const ensureIncident = async () => {
    const res  = await fetch(`${API}/alerts/${alertId}/incident`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not open an incident for this alert.");
    return data;
  };

  const openIncident = async () => {
    setBusy("incident"); setError(null);
    try {
      const incident = await ensureIncident();
      setSelected(incident.id);
      setPage("incident_detail");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const exportPDF = async () => {
    setBusy("pdf"); setError(null);
    try {
      const incident = await ensureIncident();
      const res  = await fetch(`${API}/incidents/${incident.id}/report`);
      const blob = await res.blob();
      const url  = window.URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `incident_INC-00${incident.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message || "Could not generate the PDF.");
    } finally {
      setBusy(null);
    }
  };

  if (!alert) return <div style={{ padding: 24, color: "var(--ww-muted)" }}>Loading…</div>;
  const sev = SEV_CONFIG[alert.severity] || SEV_CONFIG.info;
  const abuseColor = alert.abuse_score >= 70 ? "#D85A30" : alert.abuse_score >= 30 ? "#BA7517" : "#1D9E75";
  return (
    <>
      <Topbar title={alert.title}>
        <button onClick={() => setPage("alerts")} style={{ fontSize: 12, color: "var(--ww-muted)", background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, order: -1 }}>
          <i className="ti ti-arrow-left" aria-hidden="true" /> Alerts
        </button>
        <TopBtn icon="folder-plus" label={busy === "incident" ? "Opening…" : "Open incident"} accent onClick={openIncident} />
        <TopBtn icon="file-type-pdf" label={busy === "pdf" ? "Generating…" : "Export PDF"} onClick={exportPDF} />
      </Topbar>
      {error && (
        <div style={{ margin: "0 16px", marginTop: 12, padding: "9px 12px", borderRadius: 8, background: "#FAECE7" }}>
          <span style={{ fontSize: 12, color: "#712B13" }}>{error}</span>
        </div>
      )}
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <Card>
            <CardTitle icon="info-circle">Alert details</CardTitle>
            {[
              ["Severity", <Badge label={alert.severity} config={sev} />],
              ["Rule", alert.rule_name || alert.rule],
              ["Source IP", <code style={{ fontSize: 11, background: "var(--ww-surface)", padding: "1px 6px", borderRadius: 4 }}>{alert.source_ip}</code>],
              ["Log type", alert.log_type?.toUpperCase()],
              ["Detected", new Date(alert.created_at).toLocaleString()],
              ["Status", <Badge label={alert.status.replace("_"," ")} config={STATUS_CONFIG[alert.status]} />],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 10, padding: "5px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
                <span style={{ fontSize: 11, color: "var(--ww-muted)", minWidth: 100 }}>{k}</span>
                <span style={{ fontSize: 11, color: "var(--ww-text)" }}>{v}</span>
              </div>
            ))}
          </Card>
          <Card>
            <CardTitle icon="world">AbuseIPDB — {alert.source_ip}</CardTitle>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: 36, fontWeight: 500, color: abuseColor, lineHeight: 1 }}>{alert.abuse_score ?? "—"}</span>
              <span style={{ fontSize: 12, color: "var(--ww-muted)" }}>/ 100 confidence</span>
            </div>
            <AbuseBar score={alert.abuse_score || 0} />
            <div style={{ fontSize: 11, color: "var(--ww-muted)", lineHeight: 1.7, marginTop: 8 }}>
              <div>Country: <span style={{ color: "var(--ww-text)" }}>{alert.abuse_country}</span></div>
            </div>
          </Card>
        </div>
        <Card style={{ marginBottom: 12 }}>
          <CardTitle icon="book">What this alert means</CardTitle>
          <p style={{ fontSize: 13, color: "var(--ww-muted)", lineHeight: 1.75, margin: 0 }}>{alert.description}</p>
        </Card>
        <Card>
          <CardTitle icon="list">Raw log evidence</CardTitle>
          {["09:23:01","09:23:04","09:23:08","09:23:12","09:23:17"].map((t, i) => (
            <div key={i} style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-muted)", padding: "5px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
              Jun 4 {t} webserver sshd[1234]: Failed password for {["root","admin","ubuntu","user","deploy"][i]} from {alert.source_ip} port 22 ssh2
            </div>
          ))}
        </Card>
      </div>
    </>
  );
}

export { Alerts, AlertDetail };
