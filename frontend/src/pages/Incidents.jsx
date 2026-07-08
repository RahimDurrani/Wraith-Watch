
import { useFetch }                from "../hooks/useFetch";
import { API, SEV_CONFIG,
         STATUS_CONFIG }           from "../utils/constants";
import { Badge, Card, CardTitle,
         Topbar, TopBtn }          from "../components/UI";

function Incidents({ setPage, setSelected }) {
  const { data: incidents } = useFetch(`${API}/incidents`);
  return (
    <>
      <Topbar title="Incidents">
        <TopBtn icon="plus" label="New incident" accent />
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
              <span style={{ marginLeft: "auto", color: "#378ADD", fontWeight: 500 }}>View →</span>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}

function IncidentDetail({ incidentId, setPage }) {
  const { data: inc } = useFetch(`${API}/incidents/${incidentId}`);
  if (!inc) return <div style={{ padding: 24, color: "var(--ww-muted)" }}>Loading…</div>;
  return (
    <>
      <Topbar title={inc.title}>
        <button onClick={() => setPage("incidents")} style={{ fontSize: 12, color: "var(--ww-muted)", background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, order: -1 }}>
          <i className="ti ti-arrow-left" aria-hidden="true" /> Incidents
        </button>
        <Badge label={inc.status} config={STATUS_CONFIG[inc.status]} />
        <TopBtn icon="file-type-pdf" label="Export PDF" />
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <Card>
            <CardTitle icon="info-circle">Incident details</CardTitle>
            {[
              ["ID",           `INC-00${inc.id}`],
              ["Severity",     <Badge label={inc.severity} config={SEV_CONFIG[inc.severity]} />],
              ["Status",       <Badge label={inc.status}   config={STATUS_CONFIG[inc.status]} />],
              ["Assigned to",  inc.analyst || "Unassigned"],
              ["Linked alerts",inc.alert_ids?.length || 0],
              ["Created",      new Date(inc.created_at).toLocaleString()],
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
            <textarea placeholder="Add a note…" style={{ width: "100%", fontSize: 12, padding: "8px 10px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", resize: "vertical", minHeight: 60 }} />
            <button style={{ marginTop: 6, fontSize: 12, padding: "5px 14px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", cursor: "pointer" }}>Add note</button>
          </div>
        </Card>
      </div>
    </>
  );
}

export { Incidents, IncidentDetail };
