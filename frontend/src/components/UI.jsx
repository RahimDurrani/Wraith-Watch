

export function Badge({ label, config }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 500, padding: "2px 8px", borderRadius: 99,
      background: config?.bg   || "#F1EFE8",
      color:      config?.text || "#444441",
      border:     `0.5px solid ${config?.border || "#B4B2A9"}`,
      display: "inline-block", whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

export function Metric({ label, value, sub, color }) {
  return (
    <div style={{
      background: "var(--ww-surface)", borderRadius: 8,
      padding: "12px 14px", border: "0.5px solid var(--ww-border)",
    }}>
      <div style={{ fontSize: 11, color: "var(--ww-muted)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 500, color: color || "var(--ww-text)", lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: "var(--ww-muted)", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

export function Card({ children, style = {} }) {
  return (
    <div style={{
      background: "var(--ww-card)",
      border: "0.5px solid var(--ww-border)",
      borderRadius: 10, padding: 14, ...style,
    }}>
      {children}
    </div>
  );
}

export function CardTitle({ icon, children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 500, color: "var(--ww-muted)",
      marginBottom: 10, display: "flex", alignItems: "center", gap: 6,
    }}>
      <i className={`ti ti-${icon}`} style={{ fontSize: 14 }} aria-hidden="true" />
      {children}
    </div>
  );
}

export function MiniBar({ data }) {
  const max = Math.max(...data);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 60 }}>
      {data.map((v, i) => (
        <div key={i} style={{
          flex: 1, borderRadius: "3px 3px 0 0", minHeight: 3,
          height: `${Math.round((v / max) * 100)}%`,
          background: `rgba(55,138,221,${0.3 + (v / max) * 0.7})`,
        }} />
      ))}
    </div>
  );
}

export function AbuseBar({ score }) {
  const color = score >= 70 ? "#D85A30" : score >= 30 ? "#BA7517" : "#1D9E75";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{
        flex: 1, height: 5, background: "var(--ww-surface)",
        borderRadius: 3, overflow: "hidden",
      }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 11, fontWeight: 500, color, minWidth: 24, textAlign: "right" }}>{score}</span>
    </div>
  );
}

export function Topbar({ title, children }) {
  return (
    <div style={{
      padding: "11px 18px", borderBottom: "0.5px solid var(--ww-border)",
      display: "flex", alignItems: "center", gap: 10,
      background: "var(--ww-card)", minHeight: 48,
    }}>
      <span style={{ fontSize: 14, fontWeight: 500, color: "var(--ww-text)", flex: 1 }}>{title}</span>
      {children}
    </div>
  );
}

export function TopBtn({ icon, label, onClick, accent }) {
  return (
    <button onClick={onClick} style={{
      fontSize: 12, padding: "5px 12px", borderRadius: 8, cursor: "pointer",
      border:      accent ? "0.5px solid #85B7EB" : "0.5px solid var(--ww-border)",
      background:  accent ? "#E6F1FB"             : "var(--ww-surface)",
      color:       accent ? "#0C447C"             : "var(--ww-muted)",
      display: "flex", alignItems: "center", gap: 5,
    }}>
      {icon && <i className={`ti ti-${icon}`} style={{ fontSize: 13 }} aria-hidden="true" />}
      {label}
    </button>
  );
}

export function Placeholder({ title, icon }) {
  return (
    <>
      <Topbar title={title} />
      <div style={{
        flex: 1, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        gap: 12, color: "var(--ww-muted)",
      }}>
        <i className={`ti ti-${icon}`} style={{ fontSize: 40 }} aria-hidden="true" />
        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--ww-text)" }}>{title}</div>
        <div style={{ fontSize: 12 }}>Coming soon.</div>
      </div>
    </>
  );
}
