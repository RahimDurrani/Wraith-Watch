import { useState } from "react";
import { useFetch } from "../hooks/useFetch";
import { API, SEV_CONFIG, STATUS_CONFIG } from "../utils/constants";
import { Badge, Card, CardTitle, Topbar, TopBtn } from "../components/UI";

function Incidents({ setPage, setSelected }) {
  const { data: incidents, reload } = useFetch(`${API}/incidents`);
  const [showNew, setShowNew] = useState(false);
  const [title, setTitle] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [description, setDesc] = useState("");
  const [analyst, setAnalyst] = useState("");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const createIncident = async () => {
    setError(null);
    if (!title.trim()) { setError("Title is required."); return; }
    setSaving(true);
    try {
      const res = await fetch(`${API}/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim(), severity, description: description.trim(), analyst: analyst.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Could not create incident.");
      } else {
        setShowNew(false);
        setTitle(""); setDesc(""); setAnalyst(""); setSeverity("medium");
        reload();
      }
    } catch {
      setError("Could not reach the backend. Is Flask running?");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Topbar title="Incidents">
        <TopBtn icon="refresh" label="Refresh" onClick={reload} />
        <TopBtn icon="plus" label="New incident" accent onClick={() => setShowNew(true)} />
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        {(incidents || []).map(inc => (
          <Card key={inc.id} style={{ marginBottom: 10, cursor: "pointer" }}
            onClick={() => { setSelected(inc.id); setPage("incident_detail"); }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-muted)", minWidth: 60 }}>INC-00{inc.id}</span>
              <Badge label={inc.severity} config={SEV_CONFIG[inc.severity]} />
              <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: "var(--ww-text)" }}>{inc.title}</span>
              <Badge label={inc.status} config={STATUS_CONFIG[inc.status]} />
            </div>
            <p style={{ fontSize: 12, color: "var(--ww-muted)", margin: "0 0 10px", lineHeight: 1.6 }}>{inc.description}</p>
            <div style={{ display: "flex", gap: 16, fontSize: 11, color: "var(--ww-muted)", alignItems: "center" }}>
              <span><i className="ti ti-user" aria-hidden="true" style={{ marginRight: 4 }} />{inc.analyst || "Unassigned"}</span>
              <span><i className="ti ti-bell" aria-hidden="true" style={{ marginRight: 4 }} />{inc.alert_ids?.length || 0} alerts</span>
              <span><i className="ti ti-clock" aria-hidden="true" style={{ marginRight: 4 }} />{new Date(inc.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
              <button
                onClick={(e) => { e.stopPropagation(); setSelected(inc.id); setPage("incident_detail"); }}
                style={{ marginLeft: "auto", color: "#378ADD", fontWeight: 500, fontSize: 11, background: "none", border: "none", cursor: "pointer", padding: 0 }}>
                View →
              </button>
            </div>
          </Card>
        ))}
      </div>

      {/* New incident modal */}
      {showNew && (
        <div onClick={() => setShowNew(false)}
          style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ width: 420, background: "var(--ww-card)", borderRadius: 14, border: "0.5px solid var(--ww-border)", padding: 20 }}>
            <div style={{ fontSize: 15, fontWeight: 500, color: "var(--ww-text)", marginBottom: 16 }}>New incident</div>

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Title</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Suspicious login from unknown IP" autoFocus
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14 }} />

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Severity</label>
            <select value={severity} onChange={e => setSeverity(e.target.value)}
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14 }}>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Assigned analyst (optional)</label>
            <input value={analyst} onChange={e => setAnalyst(e.target.value)} placeholder="e.g. Alice"
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14 }} />

            <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--ww-text)", marginBottom: 5 }}>Description (optional)</label>
            <textarea value={description} onChange={e => setDesc(e.target.value)} placeholder="What happened?"
              style={{ width: "100%", fontSize: 13, padding: "9px 12px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", marginBottom: 14, resize: "vertical", minHeight: 70 }} />

            {error && (
              <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 12px", borderRadius: 8, background: "#FAECE7", marginBottom: 14 }}>
                <i className="ti ti-alert-circle" aria-hidden="true" style={{ fontSize: 14, color: "#712B13" }} />
                <span style={{ fontSize: 12, color: "#712B13" }}>{error}</span>
              </div>
            )}

            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button onClick={() => setShowNew(false)}
                style={{ fontSize: 12, padding: "8px 16px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-muted)", cursor: "pointer" }}>
                Cancel
              </button>
              <button onClick={createIncident} disabled={saving}
                style={{ fontSize: 12, fontWeight: 500, padding: "8px 16px", borderRadius: 8, border: "none", background: "#378ADD", color: "#fff", cursor: saving ? "default" : "pointer" }}>
                {saving ? "Creating…" : "Create incident"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function IncidentDetail({ incidentId, setPage }) {
  const { data: inc, reload } = useFetch(`${API}/incidents/${incidentId}`);
  const [noteText, setNoteText] = useState("");
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);

  if (!inc) return <div style={{ padding: 24, color: "var(--ww-muted)" }}>Loading…</div>;

  // Download the forensic PDF report
  const exportPDF = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${API}/incidents/${inc.id}/report`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `incident_INC-00${inc.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Could not generate the PDF. Is the backend running?");
    } finally {
      setExporting(false);
    }
  };

  // Add an analyst note
  const addNote = async () => {
    if (!noteText.trim()) return;
    setSaving(true);
    try {
      await fetch(`${API}/incidents/${inc.id}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: noteText.trim(), author: "analyst" }),
      });
      setNoteText("");
      reload();
    } catch {
      alert("Could not save the note.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Topbar title={inc.title}>
        <button onClick={() => setPage("incidents")} style={{ fontSize: 12, color: "var(--ww-muted)", background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, order: -1 }}>
          <i className="ti ti-arrow-left" aria-hidden="true" /> Incidents
        </button>
        <Badge label={inc.status} config={STATUS_CONFIG[inc.status]} />
        <TopBtn icon="file-type-pdf" label={exporting ? "Generating…" : "Export PDF"} onClick={exportPDF} />
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <Card>
            <CardTitle icon="info-circle">Incident details</CardTitle>
            {[
              ["ID", `INC-00${inc.id}`],
              ["Severity", <Badge label={inc.severity} config={SEV_CONFIG[inc.severity]} />],
              ["Status", <Badge label={inc.status} config={STATUS_CONFIG[inc.status]} />],
              ["Assigned to", inc.analyst || "Unassigned"],
              ["Linked alerts",inc.alert_ids?.length || 0],
              ["Created", new Date(inc.created_at).toLocaleString()],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 10, padding: "5px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
                <span style={{ fontSize: 11, color: "var(--ww-muted)", minWidth: 100 }}>{k}</span>
                <span style={{ fontSize: 11, color: "var(--ww-text)" }}>{v}</span>
              </div>
            ))}
          </Card>
          <Card>
            <CardTitle icon="timeline">Audit trail</CardTitle>
            {(inc.audit || []).map((a, i) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "6px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
                <span style={{ fontSize: 10, color: "var(--ww-muted)", minWidth: 36 }}>{a.time}</span>
                <span style={{ fontSize: 11, color: "var(--ww-text)" }}>{a.action}</span>
                <span style={{ fontSize: 10, color: "var(--ww-muted)", marginLeft: "auto" }}>{a.user}</span>
              </div>
            ))}
          </Card>
        </div>
        <Card style={{ marginBottom: 12 }}>
          <CardTitle icon="file-description">Description</CardTitle>
          <p style={{ fontSize: 13, color: "var(--ww-muted)", lineHeight: 1.75, margin: 0 }}>{inc.description}</p>
        </Card>
        <Card>
          <CardTitle icon="message-circle">Analyst notes</CardTitle>
          {(inc.notes || []).map((n, i) => (
            <div key={i} style={{ padding: "10px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                <div style={{ width: 22, height: 22, borderRadius: "50%", background: "#E6F1FB", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 500, color: "#0C447C" }}>{n.author[0]}</div>
                <span style={{ fontSize: 12, fontWeight: 500, color: "var(--ww-text)" }}>{n.author}</span>
                <span style={{ fontSize: 10, color: "var(--ww-muted)", marginLeft: "auto" }}>{new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
              </div>
              <p style={{ fontSize: 12, color: "var(--ww-muted)", margin: "0 0 0 30px", lineHeight: 1.65 }}>{n.content}</p>
            </div>
          ))}
          <div style={{ marginTop: 12 }}>
            <textarea value={noteText} onChange={e => setNoteText(e.target.value)}
              placeholder="Add a note…"
              style={{ width: "100%", fontSize: 12, padding: "8px 10px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", resize: "vertical", minHeight: 60 }} />
            <button onClick={addNote} disabled={saving || !noteText.trim()}
              style={{ marginTop: 6, fontSize: 12, padding: "5px 14px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: saving ? "var(--ww-surface)" : "#E6F1FB", color: saving ? "var(--ww-muted)" : "#0C447C", cursor: saving || !noteText.trim() ? "default" : "pointer", fontWeight: 500 }}>
              {saving ? "Saving…" : "Add note"}
            </button>
          </div>
        </Card>
      </div>
    </>
  );
}

export { Incidents, IncidentDetail };
