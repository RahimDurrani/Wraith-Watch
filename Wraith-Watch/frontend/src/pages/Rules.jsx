// src/pages/Rules.jsx
// ─────────────────────────────────────────────────────────
// Detection rules page — view and enable/disable the
// rule engine's detection rules.
// ─────────────────────────────────────────────────────────
import { useState, useEffect } from "react";
import { API, SEV_CONFIG, LOG_TYPE_COLORS } from "../utils/constants";
import { Badge, Topbar } from "../components/UI";

function Rules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    fetch(`${API}/rules`)
      .then(r => r.json())
      .then(d => { setRules(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const toggle = async (id) => {
    // optimistic update
    setRules(rs => rs.map(r => r.id === id ? { ...r, is_enabled: !r.is_enabled } : r));
    try {
      await fetch(`${API}/rules/${id}/toggle`, { method: "PATCH" });
    } catch {
      load(); // revert on failure
    }
  };

  const enabledCount = rules.filter(r => r.is_enabled).length;

  return (
    <>
      <Topbar title="Detection rules">
        <span style={{ fontSize: 12, color: "var(--ww-muted)" }}>
          {enabledCount} of {rules.length} enabled
        </span>
      </Topbar>
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
        {loading && <div style={{ padding: 24, color: "var(--ww-muted)", fontSize: 13 }}>Loading rules…</div>}

        {!loading && rules.map(rule => {
          const sev = SEV_CONFIG[rule.severity] || SEV_CONFIG.info;
          const tc = LOG_TYPE_COLORS[rule.log_type] || {};
          return (
            <div key={rule.id} style={{
              background: "var(--ww-card)", border: "0.5px solid var(--ww-border)",
              borderRadius: 10, padding: 14, marginBottom: 10,
              opacity: rule.is_enabled ? 1 : 0.6,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <i className="ti ti-shield-check" aria-hidden="true" style={{ fontSize: 16, color: rule.is_enabled ? "#378ADD" : "var(--ww-muted)" }} />
                <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: "var(--ww-text)", fontFamily: "monospace" }}>
                  {rule.name}
                </span>
                <Badge label={rule.severity} config={sev} />
                <span style={{ fontSize: 9, padding: "1px 6px", borderRadius: 99, background: tc.bg || "var(--ww-surface)", color: tc.text || "var(--ww-muted)", textTransform: "uppercase", fontWeight: 500 }}>
                  {rule.log_type}
                </span>

                {/* Toggle switch */}
                <button
                  onClick={() => toggle(rule.id)}
                  aria-label={rule.is_enabled ? "Disable rule" : "Enable rule"}
                  style={{
                    width: 40, height: 22, borderRadius: 99, border: "none", cursor: "pointer",
                    background: rule.is_enabled ? "#1D9E75" : "var(--ww-border)",
                    position: "relative", transition: "background .15s", flexShrink: 0,
                  }}
                >
                  <span style={{
                    position: "absolute", top: 2, left: rule.is_enabled ? 20 : 2,
                    width: 18, height: 18, borderRadius: "50%", background: "#fff",
                    transition: "left .15s",
                  }} />
                </button>
              </div>

              <p style={{ fontSize: 12, color: "var(--ww-muted)", margin: "0 0 8px", lineHeight: 1.6 }}>
                {rule.description}
              </p>

              <div style={{ display: "flex", gap: 16, fontSize: 11, color: "var(--ww-muted)", alignItems: "center" }}>
                <span style={{ fontFamily: "monospace" }}>
                  <i className="ti ti-regex" aria-hidden="true" style={{ marginRight: 4 }} />
                  {rule.pattern}
                </span>
                {rule.threshold && (
                  <span style={{ marginLeft: "auto" }}>
                    <i className="ti ti-clock" aria-hidden="true" style={{ marginRight: 4 }} />
                    {rule.threshold} events / {rule.window_seconds}s
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

export default Rules;
