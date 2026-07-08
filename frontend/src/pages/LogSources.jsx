
import { useFetch }         from "../hooks/useFetch";
import { API, SRC_STATUS } from "../utils/constants";
import { Topbar, TopBtn }  from "../components/UI";

function LogSources() {
  const { data: sources } = useFetch(`${API}/log-sources`);
  return (
    <>
      <Topbar title="Log sources">
        <TopBtn icon="plus"     label="Add source" accent />
        <TopBtn icon="refresh"  label="Refresh" />
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 16 }}>
          {["active","stale","silent"].map(st => {
            const count = (sources || []).filter(s => s.status === st).length;
            const cfg   = SRC_STATUS[st];
            return (
              <div key={st} style={{ background: cfg.badge_bg, borderRadius: 8, padding: "12px 14px", border: `0.5px solid ${cfg.dot}44` }}>
                <div style={{ fontSize: 11, color: cfg.badge_text, textTransform: "capitalize", marginBottom: 4 }}>{st} sources</div>
                <div style={{ fontSize: 28, fontWeight: 500, color: cfg.dot }}>{count}</div>
              </div>
            );
          })}
        </div>
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
                <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{s.hostname}</span>
                <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{s.minutes_ago === 0 ? "just now" : `${s.minutes_ago}m ago`}</span>
                <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{s.total_logs.toLocaleString()}</span>
                <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 99, background: cfg.badge_bg, color: cfg.badge_text, display: "inline-block", textAlign: "center" }}>{s.status}</span>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

export default LogSources;
