// src/pages/LogSources.jsx
import { useState, useEffect } from "react";
import { API, SRC_STATUS } from "../utils/constants";
import { Topbar, TopBtn } from "../components/UI";

function LogSources() {
  const [sources, setSources] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState("syslog");
  const [hostname, setHost] = useState("");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    fetch(`${API}/log-sources`)
      .then(r => r.json())
      .then(setSources)
      .catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const addSource = async () => {
    setError(null);
    if (!name.trim()) { setError("Source name is required."); return; }
    setSaving(true);
    try {
      const res = await fetch(`${API}/log-sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), type, hostname: hostname.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Could not add source.");
      } else {
        setShowAdd(false);
        setName(""); setHost(""); setType("syslog");
        load();
      }
    } catch {
      setError("Could not reach the backend. Is Flask running?");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Topbar title="Log sources">
        <TopBtn icon="plus" label="Add source" accent onClick={() => setShowAdd(true)} />
        <TopBtn icon="refresh" label="Refresh" onClick={load} />
      </Topbar>

      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        {/* Status summary tiles */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 16 }}>
          {["active","stale","silent"].map(st => {
            const count = (sources || []).filter(s => s.status === st).length;
            const cfg = SRC_STATUS[st];
            return (
              <div key={st} style={{ background: cfg.badge_bg, borderRadius: 8, padding: "12px 14px", border: `0.5px solid ${cfg.dot}44` }}>
                <div style={{ fontSize: 11, color: cfg.badge_text, textTransform: "capitalize", marginBottom: 4 }}>{st} sources</div>
                <div style={{ fontSize: 28, fontWeight: 500, color: cfg.dot }}>{count}</div>
              </div>
            );
          })}
        </div>

        {/* Sources table */}
        <div style={{ border: "0.5px solid var(--ww-border)", borderRadius: 10, overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 70px 100px 80px 80px 80px", padding: "8px 14px", background: "var(--ww-surface)", borderBottom: "0.5px solid var(--ww-border)" }}>
            {["Source name","Type","Host","Last seen","Logs","Status"].map(h => (
              <span key={h} style={{ fontSize: 10, fontWeight: 500, color: "var(--ww-muted)" }}>{h}</span>
            ))}
          </div>
          {(sources || []).map(s => {
            const cfg = SRC_STATUS[s.status];
            return (
              <div key={s.id} style={{ display: "grid", gridTemplateColumns: "1fr 70px 100px 80px 80px 80px", padding: "10px 14px", borderBottom: "0.5px solid var(--ww-border)", background: "var(--ww-card)", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: cfg.dot }} />
                  <span style={{ fontSize: 12, color: "var(--ww-text)", fontFamily: "monospace" }}>{s.name}</span>
                </div>
                <span style={{ fontSize: 11, color: "var(--ww-muted)", textTransform: "uppercase" }}>{s.type}</span>
                <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{s.hostname || "—"}</span>
                <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{s.minutes_ago === 0 ? "just now" : `${s.minutes_ago}m ago`}</span>
                <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{s.total_logs.toLocaleString()}</span>
                <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 99, background: cfg.badge_bg, color: cfg.badge_text, display: "inline-block", textAlign: "center" }}>{s.status}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add source modal */}
      {showAdd && (
        <div
          onClick={() => setShowAdd(false)}
          style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{ width: 380, background: "var(--ww-card)", borderRadius: 14, border: "0.5px solid var(--ww-border)", padding: 20 }}
          >
            <div style={{ fontSize: 15, fontWeight: 500, color: "var(--ww-text)", marginBottom: 16 }}>Add log source</div>

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Source name</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. firewall.log" autoFocus
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14 }} />

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Type</label>
            <select value={type} onChange={e => setType(e.target.value)}
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14 }}>
              <option value="syslog">Syslog</option>
              <option value="apache">Apache / Nginx</option>
              <option value="evtx">Windows EVTX</option>
            </select>

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Hostname (optional)</label>
            <input value={hostname} onChange={e => setHost(e.target.value)} placeholder="e.g. web01"
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14 }} />

            {error && (
              <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 12px", borderRadius: 8, background: "#FAECE7", marginBottom: 14 }}>
                <i className="ti ti-alert-circle" aria-hidden="true" style={{ fontSize: 14, color: "#712B13" }} />
                <span style={{ fontSize: 12, color: "#712B13" }}>{error}</span>
              </div>
            )}

            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button onClick={() => setShowAdd(false)}
                style={{ fontSize: 12, padding: "8px 16px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-muted)", cursor: "pointer" }}>
                Cancel
              </button>
              <button onClick={addSource} disabled={saving}
                style={{ fontSize: 12, fontWeight: 500, padding: "8px 16px", borderRadius: 8, border: "none", background: "#378ADD", color: "#fff", cursor: saving ? "default" : "pointer" }}>
                {saving ? "Adding…" : "Add source"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default LogSources;
