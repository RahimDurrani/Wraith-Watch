import { useState } from "react";
import { API, LOG_TYPE_COLORS } from "../utils/constants";
import { Topbar, TopBtn } from "../components/UI";

function LogSearch() {
  const [query, setQuery] = useState("");
  const [typeFilter, setType] = useState("");
  const [results, setResults] = useState(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const runSearch = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setSearched(true);
    try {
      const params = new URLSearchParams({
        q: query.trim(),
        ...(typeFilter ? { log_type: typeFilter } : {}),
        limit: 200,
      });
      const res = await fetch(`${API}/logs/search?${params}`);
      const data = await res.json();
      setResults(data.results || []);
      setTotal(data.total || 0);
    } catch {
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const highlight = (text) => {
    if (!query.trim() || !text) return text;
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <mark style={{ background: "#FFF3B0", color: "#1A1A18", borderRadius: 2 }}>
          {text.slice(idx, idx + query.length)}
        </mark>
        {text.slice(idx + query.length)}
      </>
    );
  };

  return (
    <>
      <Topbar title="Log search" />
      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>

        {/* Search bar */}
        <form onSubmit={runSearch} style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          <div style={{ position: "relative", flex: 1 }}>
            <i className="ti ti-search" aria-hidden="true"
              style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", fontSize: 15, color: "var(--ww-muted)" }} />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search by IP, hostname, message, or filename…"
              autoFocus
              style={{ width: "100%", fontSize: 13, padding: "9px 12px 9px 32px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)" }}
            />
          </div>
          <select value={typeFilter} onChange={e => setType(e.target.value)}
            style={{ fontSize: 12, padding: "0 10px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)" }}>
            <option value="">All types</option>
            <option value="apache">Apache</option>
            <option value="syslog">Syslog</option>
            <option value="evtx">EVTX</option>
          </select>
          <button type="submit" style={{
            fontSize: 13, fontWeight: 500, padding: "0 18px", borderRadius: 8,
            border: "none", background: "#378ADD", color: "#fff", cursor: "pointer",
          }}>Search</button>
        </form>

        {/* Result count */}
        {searched && !loading && (
          <div style={{ fontSize: 12, color: "var(--ww-muted)", marginBottom: 10 }}>
            {total === 0 ? "No matching log entries found." : `${total} matching ${total === 1 ? "entry" : "entries"}${total > 200 ? " (showing first 200)" : ""}`}
          </div>
        )}

        {loading && <div style={{ padding: 24, textAlign: "center", color: "var(--ww-muted)", fontSize: 13 }}>Searching…</div>}

        {/* Results */}
        {!loading && results && results.length > 0 && (
          <div style={{ border: "0.5px solid var(--ww-border)", borderRadius: 10, overflow: "hidden" }}>
            <div style={{ display: "grid", gridTemplateColumns: "70px 130px 110px 1fr", padding: "8px 14px", background: "var(--ww-surface)", borderBottom: "0.5px solid var(--ww-border)" }}>
              {["Type", "Source IP", "Host", "Message"].map(h => (
                <span key={h} style={{ fontSize: 10, fontWeight: 500, color: "var(--ww-muted)" }}>{h}</span>
              ))}
            </div>
            {results.map((r, i) => {
              const tc = LOG_TYPE_COLORS[r.log_type] || {};
              return (
                <div key={r.id || i} style={{ display: "grid", gridTemplateColumns: "70px 130px 110px 1fr", padding: "8px 14px", borderBottom: "0.5px solid var(--ww-border)", background: "var(--ww-card)", alignItems: "center" }}>
                  <span style={{ fontSize: 9, padding: "1px 6px", borderRadius: 99, background: tc.bg || "var(--ww-surface)", color: tc.text || "var(--ww-muted)", textTransform: "uppercase", fontWeight: 500, display: "inline-block", width: "fit-content" }}>{r.log_type}</span>
                  <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-muted)" }}>{highlight(r.source_ip) || "—"}</span>
                  <span style={{ fontSize: 11, color: "var(--ww-muted)" }}>{highlight(r.hostname) || "—"}</span>
                  <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{highlight(r.raw_message)}</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Empty state before first search */}
        {!searched && !loading && (
          <div style={{ padding: 40, textAlign: "center", color: "var(--ww-muted)" }}>
            <i className="ti ti-search" style={{ fontSize: 36, display: "block", marginBottom: 10 }} aria-hidden="true" />
            <div style={{ fontSize: 13 }}>Search across all ingested log entries.</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>Try an IP address, hostname, or keyword like "failed password".</div>
          </div>
        )}
      </div>
    </>
  );
}

export default LogSearch;
