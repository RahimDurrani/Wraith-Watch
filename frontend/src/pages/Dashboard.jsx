
import { useFetch }                from "../hooks/useFetch";
import { API, SEV_CONFIG,
         STATUS_CONFIG, SRC_STATUS }from "../utils/constants";
import { Badge, Metric, Card,
         CardTitle, MiniBar,
         AbuseBar, Topbar, TopBtn } from "../components/UI";

function Dashboard({ setPage, setSelected }) {
  const { data: stats }     = useFetch(`${API}/stats`);
  const { data: alerts }    = useFetch(`${API}/alerts`);
  const { data: sources }   = useFetch(`${API}/log-sources`);
  const { data: chart }     = useFetch(`${API}/chart/alerts`);
  const { data: incidents } = useFetch(`${API}/incidents`);

  const topAlerts = alerts ? alerts.slice(0, 5) : [];
  const topIPs    = alerts
    ? [...new Map(alerts.filter(a => a.source_ip && a.abuse_score).map(a => [a.source_ip, a])).values()].slice(0, 4)
    : [];

  return (
    <>
      <Topbar title="Overview">
        <TopBtn icon="upload"  label="Upload logs" />
        <TopBtn icon="refresh" label="Refresh" />
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>

        {/* Metric tiles */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 14 }}>
          <Metric label="Open alerts"    value={stats?.open_alerts    ?? "—"} sub="↑ 3 last hour"   color="#D85A30" />
          <Metric label="Critical"       value={stats?.critical        ?? "—"} sub="Needs attention"  color="#D85A30" />
          <Metric label="Open incidents" value={stats?.open_incidents  ?? "—"} sub="1 unassigned"     color="#BA7517" />
          <Metric label="Log sources"    value={stats?.log_sources     ?? "—"} sub={`${stats?.active_sources ?? 0} active`} color="#1D9E75" />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          {/* Top threats */}
          <Card>
            <CardTitle icon="bell">Top threats</CardTitle>
            {topAlerts.map(a => (
              <div key={a.id}
                onClick={() => { setSelected(a.id); setPage("alert_detail"); }}
                style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 0", borderBottom: "0.5px solid var(--ww-border)", cursor: "pointer" }}>
                <Badge label={a.severity} config={SEV_CONFIG[a.severity]} />
                <span style={{ flex: 1, fontSize: 11, color: "var(--ww-text)" }}>{a.title}</span>
                <span style={{ fontSize: 10, color: "var(--ww-muted)", whiteSpace: "nowrap" }}>
                  {new Date(a.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            ))}
          </Card>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {/* Chart */}
            <Card>
              <CardTitle icon="chart-bar">Alert volume — last 12h</CardTitle>
              {chart && <MiniBar data={chart.data} />}
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                {["00:00","","","","","","12:00","","","","","now"].map((l, i) => (
                  <span key={i} style={{ fontSize: 9, color: "var(--ww-muted)" }}>{l}</span>
                ))}
              </div>
            </Card>

            {/* Log source health */}
            <Card>
              <CardTitle icon="heart-rate-monitor">Log source health</CardTitle>
              {(sources || []).slice(0, 4).map(s => (
                <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: SRC_STATUS[s.status]?.dot, flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: 11, color: "var(--ww-text)" }}>{s.name}</span>
                  <span style={{ fontSize: 10, color: "var(--ww-muted)" }}>{s.minutes_ago === 0 ? "just now" : `${s.minutes_ago}m ago`}</span>
                  <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 99, background: SRC_STATUS[s.status]?.badge_bg, color: SRC_STATUS[s.status]?.badge_text }}>{s.status}</span>
                </div>
              ))}
            </Card>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {/* Recent incidents */}
          <Card>
            <CardTitle icon="folder-open">Recent incidents</CardTitle>
            {(incidents || []).map(inc => (
              <div key={inc.id}
                onClick={() => { setSelected(inc.id); setPage("incident_detail"); }}
                style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 0", borderBottom: "0.5px solid var(--ww-border)", cursor: "pointer" }}>
                <Badge label={inc.status} config={STATUS_CONFIG[inc.status]} />
                <span style={{ flex: 1, fontSize: 11, color: "var(--ww-text)" }}>{inc.title}</span>
                <span style={{ fontSize: 10, color: "var(--ww-muted)" }}>{inc.analyst || "Unassigned"}</span>
              </div>
            ))}
          </Card>

          {/* IP reputation */}
          <Card>
            <CardTitle icon="world">IP reputation — AbuseIPDB</CardTitle>
            {topIPs.map(a => (
              <div key={a.source_ip} style={{ padding: "6px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-text)", minWidth: 110 }}>{a.source_ip}</span>
                  <span style={{ fontSize: 10, color: "var(--ww-muted)" }}>{a.abuse_country}</span>
                </div>
                <AbuseBar score={a.abuse_score} />
              </div>
            ))}
          </Card>
        </div>

      </div>
    </>
  );
}

export default Dashboard;
