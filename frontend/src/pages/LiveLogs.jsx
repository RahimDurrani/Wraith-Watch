import { useState, useEffect, useRef } from "react";
import { API, FLAG_COLORS,
         LOG_TYPE_COLORS }             from "../utils/constants";
import { Topbar, TopBtn }              from "../components/UI";

function LiveLogs() {
  const [logs, setLogs]             = useState([]);
  const [lastId, setLastId]         = useState(0);
  const [paused, setPaused]         = useState(false);
  const [search, setSearch]         = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [stats, setStats]           = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [actionMsg, setActionMsg]     = useState(null);   // feedback after an action
  const [busy, setBusy]               = useState(false);

  // Extract the first IPv4 address from a log message
  const extractIP = (msg) => {
    const m = (msg || "").match(/\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b/);
    return m ? m[1] : null;
  };

  // Create an incident from the selected log entry
  const createIncidentFromLog = async (log) => {
    setBusy(true);
    setActionMsg(null);
    try {
      const res  = await fetch(`${API}/incidents/from-log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message:    log.message,
          log_type:   log.log_type,
          hostname:   log.hostname,
          flag_level: log.flag_level,
          source_ip:  extractIP(log.message),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setActionMsg({ type: "ok", text: `Incident INC-00${data.id} created and saved.` });
      } else {
        setActionMsg({ type: "err", text: data.error || "Could not create incident." });
      }
    } catch {
      setActionMsg({ type: "err", text: "Could not reach the backend." });
    } finally {
      setBusy(false);
    }
  };

  // Look up the log's IP in AbuseIPDB
  const lookupIP = async (log) => {
    const ip = extractIP(log.message);
    if (!ip) { setActionMsg({ type: "err", text: "No IP address found in this log." }); return; }
    setBusy(true);
    setActionMsg(null);
    try {
      const res  = await fetch(`${API}/ip-lookup?ip=${encodeURIComponent(ip)}`);
      const data = await res.json();
      if (data.available) {
        setActionMsg({ type: "ok", text: `${ip}: abuse score ${data.abuse_score}/100 (${data.abuse_country}).` });
      } else {
        setActionMsg({ type: "info", text: `${ip}: ${data.message}` });
      }
    } catch {
      setActionMsg({ type: "err", text: "Could not reach the backend." });
    } finally {
      setBusy(false);
    }
  };
  const [autoScroll, setAutoScroll] = useState(true);
  const bottomRef  = useRef(null);
  const tableRef   = useRef(null);
  const pausedRef  = useRef(paused);
  const lastIdRef  = useRef(lastId);

  pausedRef.current = paused;
  lastIdRef.current = lastId;

  // ── Polling for new log lines every 2s ──────────────────────────────────────
  useEffect(() => {
    const poll = async () => {
      if (pausedRef.current) return;
      try {
        const params = new URLSearchParams({
          since: lastIdRef.current,
          limit: 100,
          ...(typeFilter  ? { log_type: typeFilter } : {}),
          ...(flaggedOnly ? { flagged: "true" }      : {}),
          ...(search      ? { search }               : {}),
        });
        const res  = await fetch(`${API}/logs/recent?${params}`);
        const data = await res.json();
        if (data.logs?.length) {
          setLogs(prev => {
            const combined = [...prev, ...data.logs].slice(-300);
            return combined;
          });
          setLastId(data.last_id);
        }
      } catch { /* backend offline */ }
    };

    poll(); // immediate first call
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [typeFilter, flaggedOnly, search]);

  // ── Fetch stats independently every 3s ──────────────────────────────────────
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res  = await fetch(`${API}/logs/stats`);
        const data = await res.json();
        setStats(data);
      } catch {}
    };
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  // ── Auto-scroll to bottom when new logs arrive ───────────────────────────────
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  // Detect if user manually scrolled up — pause auto-scroll
  const handleScroll = () => {
    if (!tableRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = tableRef.current;
    const nearBottom = scrollHeight - scrollTop - clientHeight < 60;
    setAutoScroll(nearBottom);
  };

  // Clear filters and reset log buffer
  const handleClear = () => {
    setLogs([]);
    setLastId(0);
    setSearch("");
    setTypeFilter("");
    setFlaggedOnly(false);
  };

  const visibleLogs = logs.filter(l => {
    if (typeFilter  && l.log_type !== typeFilter)  return false;
    if (flaggedOnly && !l.flagged)                 return false;
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())
               && !l.hostname.toLowerCase().includes(search.toLowerCase())
               && !l.source.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const highlightSearch = (text) => {
    if (!search) return text;
    const idx = text.toLowerCase().indexOf(search.toLowerCase());
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <mark style={{ background: "#FFF3B0", color: "#1A1A18", borderRadius: 2 }}>
          {text.slice(idx, idx + search.length)}
        </mark>
        {text.slice(idx + search.length)}
      </>
    );
  };

  return (
    <>
      <Topbar title="Live logs">
        {/* Stat pills */}
        {stats && (
          <div style={{ display: "flex", gap: 6, marginRight: 6 }}>
            {[
              { label: `${stats.total} total`,    bg: "var(--ww-surface)", text: "var(--ww-muted)" },
              { label: `${stats.flagged} flagged`, bg: "#FAECE7",          text: "#712B13"          },
              { label: `${stats.by_type?.apache ?? 0} apache`, bg: "#EAF3DE", text: "#27500A" },
              { label: `${stats.by_type?.syslog ?? 0} syslog`, bg: "#E6F1FB", text: "#0C447C" },
              { label: `${stats.by_type?.evtx   ?? 0} evtx`,   bg: "#EEEDFE", text: "#3C3489" },
            ].map(p => (
              <span key={p.label} style={{
                fontSize: 10, padding: "3px 8px", borderRadius: 99,
                background: p.bg, color: p.text, fontWeight: 500,
                border: "0.5px solid var(--ww-border)",
              }}>{p.label}</span>
            ))}
          </div>
        )}

        {/* Search */}
        <div style={{ position: "relative" }}>
          <i className="ti ti-search" style={{ position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)", fontSize: 13, color: "var(--ww-muted)" }} aria-hidden="true" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search logs…"
            style={{ fontSize: 12, padding: "5px 10px 5px 28px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)", width: 160 }}
          />
        </div>

        {/* Type filter */}
        <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setLogs([]); setLastId(0); }}
          style={{ fontSize: 12, padding: "5px 8px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)", color: "var(--ww-text)" }}>
          <option value="">All sources</option>
          <option value="apache">Apache</option>
          <option value="syslog">Syslog</option>
          <option value="evtx">EVTX</option>
        </select>

        {/* Flagged toggle */}
        <button onClick={() => { setFlaggedOnly(f => !f); setLogs([]); setLastId(0); }}
          style={{ fontSize: 12, padding: "5px 10px", borderRadius: 8, border: "0.5px solid var(--ww-border)", background: flaggedOnly ? "#FAECE7" : "var(--ww-surface)", color: flaggedOnly ? "#712B13" : "var(--ww-muted)", cursor: "pointer", fontWeight: flaggedOnly ? 500 : 400 }}>
          <i className="ti ti-flag" aria-hidden="true" style={{ marginRight: 4 }} />
          Flagged only
        </button>

        {/* Pause / resume */}
        <TopBtn
          icon={paused ? "player-play" : "player-pause"}
          label={paused ? "Resume" : "Pause"}
          onClick={() => setPaused(p => !p)}
          accent={paused}
        />

        {/* Clear */}
        <TopBtn icon="trash" label="Clear" onClick={handleClear} />
      </Topbar>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {/* ── Log table ─────────────────────────────────────────────────────── */}
        <div
          ref={tableRef}
          onScroll={handleScroll}
          style={{ flex: 1, overflowY: "auto", fontFamily: "monospace", fontSize: 11 }}
        >
          {/* Header row */}
          <div style={{
            display: "grid", gridTemplateColumns: "60px 54px 80px 110px 1fr",
            padding: "6px 14px", background: "var(--ww-surface)",
            borderBottom: "0.5px solid var(--ww-border)",
            position: "sticky", top: 0, zIndex: 2,
          }}>
            {["Time","Level","Type","Host","Message"].map(h => (
              <span key={h} style={{ fontSize: 10, fontWeight: 500, color: "var(--ww-muted)", fontFamily: "sans-serif" }}>{h}</span>
            ))}
          </div>

          {visibleLogs.length === 0 && (
            <div style={{ padding: 32, textAlign: "center", color: "var(--ww-muted)", fontSize: 12, fontFamily: "sans-serif" }}>
              <i className="ti ti-activity" style={{ fontSize: 32, display: "block", marginBottom: 8 }} aria-hidden="true" />
              {paused ? (
                "Paused — press Resume to continue streaming."
              ) : stats && stats.total > 0 ? (
                // The generator IS producing entries (stats is fetched with no
                // filters) — they're just all excluded by the current Type /
                // Flagged / Search filter. Showing "waiting" here would be
                // misleading, so say what's actually happening instead.
                <>
                  <div style={{ marginBottom: 10 }}>
                    {stats.total} log{stats.total === 1 ? "" : "s"} received overall, but none match your current filter.
                  </div>
                  <button onClick={handleClear} style={{
                    fontSize: 12, fontWeight: 500, padding: "6px 14px", borderRadius: 8,
                    border: "0.5px solid var(--ww-border)", background: "var(--ww-surface)",
                    color: "#378ADD", cursor: "pointer",
                  }}>
                    Clear filters
                  </button>
                </>
              ) : (
                "Waiting for log entries…"
              )}
            </div>
          )}

          {visibleLogs.map(log => {
            const fc   = FLAG_COLORS[log.flag_level] || FLAG_COLORS.info;
            const tc   = LOG_TYPE_COLORS[log.log_type] || {};
            const isSelected = selectedLog?.id === log.id;
            return (
              <div
                key={log.id}
                onClick={() => { setSelectedLog(isSelected ? null : log); setActionMsg(null); }}
                style={{
                  display: "grid",
                  gridTemplateColumns: "60px 54px 80px 110px 1fr",
                  padding: "4px 14px",
                  borderBottom: "0.5px solid var(--ww-border)",
                  background: isSelected
                    ? "#E6F1FB"
                    : log.flagged
                    ? `${fc.bg}`
                    : "var(--ww-card)",
                  cursor: "pointer",
                  alignItems: "center",
                }}
                onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "var(--ww-surface)"; }}
                onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = log.flagged ? fc.bg : "var(--ww-card)"; }}
              >
                {/* Time */}
                <span style={{ color: "var(--ww-muted)", fontSize: 10 }}>{log.timestamp}</span>

                {/* Level dot + label */}
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: fc.dot, flexShrink: 0 }} />
                  <span style={{ fontSize: 10, color: fc.text, fontFamily: "sans-serif" }}>{log.flag_level}</span>
                </div>

                {/* Log type badge */}
                <span style={{
                  fontSize: 9, padding: "1px 6px", borderRadius: 99,
                  background: tc.bg || "var(--ww-surface)", color: tc.text || "var(--ww-muted)",
                  fontFamily: "sans-serif", textTransform: "uppercase", fontWeight: 500,
                  display: "inline-block",
                }}>{log.log_type}</span>

                {/* Hostname */}
                <span style={{ color: "var(--ww-muted)", fontSize: 10, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{log.hostname}</span>

                {/* Message */}
                <span style={{
                  color: log.flagged ? fc.text : "var(--ww-text)",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                }}>
                  {highlightSearch(log.message)}
                </span>
              </div>
            );
          })}

          {/* Pause banner */}
          {paused && (
            <div style={{ position: "sticky", bottom: 0, background: "#FAEEDA", borderTop: "0.5px solid #EF9F27", padding: "7px 14px", display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#633806" }}>
              <i className="ti ti-player-pause" aria-hidden="true" />
              Stream paused — {visibleLogs.length} lines in buffer.
              <button onClick={() => setPaused(false)} style={{ marginLeft: "auto", fontSize: 11, padding: "3px 10px", borderRadius: 6, border: "0.5px solid #EF9F27", background: "#fff", color: "#633806", cursor: "pointer" }}>Resume</button>
            </div>
          )}

          {/* Auto-scroll anchor */}
          {!paused && <div ref={bottomRef} />}
        </div>

        {/* ── Detail panel (slides in when a log row is clicked) ────────────── */}
        {selectedLog && (
          <div style={{
            width: 320, minWidth: 320, borderLeft: "0.5px solid var(--ww-border)",
            background: "var(--ww-surface)", padding: 0, display: "flex", flexDirection: "column", overflowY: "auto",
          }}>
            <div style={{ padding: "12px 14px", borderBottom: "0.5px solid var(--ww-border)", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ flex: 1, fontSize: 12, fontWeight: 500, color: "var(--ww-text)" }}>Log entry #{selectedLog.id}</span>
              <button onClick={() => setSelectedLog(null)} aria-label="Close" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ww-muted)", fontSize: 16 }}>×</button>
            </div>

            <div style={{ padding: 14 }}>
              {/* Level banner */}
              <div style={{
                padding: "8px 12px", borderRadius: 8, marginBottom: 14,
                background: FLAG_COLORS[selectedLog.flag_level]?.bg || "var(--ww-surface)",
                border: `0.5px solid ${FLAG_COLORS[selectedLog.flag_level]?.border || "var(--ww-border)"}`,
                display: "flex", alignItems: "center", gap: 8,
              }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: FLAG_COLORS[selectedLog.flag_level]?.dot }} />
                <span style={{ fontSize: 12, fontWeight: 500, color: FLAG_COLORS[selectedLog.flag_level]?.text, textTransform: "capitalize" }}>
                  {selectedLog.flag_level} {selectedLog.flagged ? "— flagged" : "— normal"}
                </span>
              </div>

              {/* Fields */}
              {[
                ["Time",     selectedLog.timestamp],
                ["Log type", selectedLog.log_type?.toUpperCase()],
                ["Source",   selectedLog.source],
                ["Hostname", selectedLog.hostname],
              ].map(([k, v]) => (
                <div key={k} style={{ display: "flex", gap: 10, padding: "6px 0", borderBottom: "0.5px solid var(--ww-border)" }}>
                  <span style={{ fontSize: 11, color: "var(--ww-muted)", minWidth: 70, fontFamily: "sans-serif" }}>{k}</span>
                  <span style={{ fontSize: 11, color: "var(--ww-text)", fontFamily: "monospace" }}>{v}</span>
                </div>
              ))}

              {/* Raw message */}
              <div style={{ marginTop: 14 }}>
                <div style={{ fontSize: 11, color: "var(--ww-muted)", fontFamily: "sans-serif", marginBottom: 6 }}>Raw message</div>
                <div style={{
                  fontSize: 11, fontFamily: "monospace", color: "var(--ww-text)",
                  background: "var(--ww-card)", border: "0.5px solid var(--ww-border)",
                  borderRadius: 8, padding: "10px 12px", lineHeight: 1.6, wordBreak: "break-all",
                }}>{selectedLog.message}</div>
              </div>

              {/* Action buttons */}
              {selectedLog.flagged && (
                <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 6 }}>
                  <button
                    onClick={() => createIncidentFromLog(selectedLog)}
                    disabled={busy}
                    style={{
                      fontSize: 12, padding: "8px 0", borderRadius: 8,
                      border: "0.5px solid #85B7EB", background: "#E6F1FB",
                      color: "#0C447C", cursor: busy ? "default" : "pointer", fontWeight: 500,
                    }}>
                    <i className="ti ti-folder-plus" aria-hidden="true" style={{ marginRight: 6 }} />
                    Create incident from this log
                  </button>
                  <button
                    onClick={() => lookupIP(selectedLog)}
                    disabled={busy}
                    style={{
                      fontSize: 12, padding: "8px 0", borderRadius: 8,
                      border: "0.5px solid var(--ww-border)", background: "var(--ww-card)",
                      color: "var(--ww-muted)", cursor: busy ? "default" : "pointer",
                    }}>
                    <i className="ti ti-world" aria-hidden="true" style={{ marginRight: 6 }} />
                    Look up IP in AbuseIPDB
                  </button>

                  {actionMsg && (
                    <div style={{
                      marginTop: 4, padding: "8px 10px", borderRadius: 8, fontSize: 11, lineHeight: 1.5,
                      background: actionMsg.type === "ok" ? "#EAF3DE" : actionMsg.type === "err" ? "#FAECE7" : "#E6F1FB",
                      color:      actionMsg.type === "ok" ? "#27500A" : actionMsg.type === "err" ? "#712B13" : "#0C447C",
                    }}>
                      {actionMsg.text}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}


export default LiveLogs;
