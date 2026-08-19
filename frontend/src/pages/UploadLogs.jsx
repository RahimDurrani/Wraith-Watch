
import { useState }                        from "react";
import { useFetch }                        from "../hooks/useFetch";
import { API }                             from "../utils/constants";
import { Card, CardTitle, Metric,
         Topbar, TopBtn }                  from "../components/UI";

const FORMAT_LABEL = {
  apache:  "Apache / Nginx",
  syslog:  "Syslog",
  evtx:    "Windows EVTX",
  unknown: "Unrecognised",
};

function UploadLogs() {
  const [dragOver,   setDragOver]   = useState(false);
  const [uploading,  setUploading]  = useState(false);
  const [result,     setResult]     = useState(null);
  const [error,      setError]      = useState(null);

  const { data: history, reload } = useFetch(`${API}/uploads`);

  const doUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res  = await fetch(`${API}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok || data.error) {
        setError(data.error || "Upload failed.");
      } else {
        setResult(data);
        reload();
      }
    } catch {
      setError("Could not reach the backend. Is Flask running on port 5000?");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    doUpload(e.dataTransfer.files?.[0]);
  };

  const handleFileInput = (e) => {
    doUpload(e.target.files?.[0]);
    e.target.value = "";
  };

  const refreshView = () => {
    setResult(null);
    setError(null);
    reload();
  };

  return (
    <>
      <Topbar title="Upload logs">
        <TopBtn icon="refresh" label="Refresh" onClick={refreshView} />
      </Topbar>

      <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>

        {/* ── Drop zone ─────────────────────────────────────────── */}
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById("ww-file-input").click()}
          style={{
            border:     `2px dashed ${dragOver ? "#378ADD" : "var(--ww-border)"}`,
            borderRadius: 12,
            padding:    "36px 20px",
            textAlign:  "center",
            background: dragOver ? "#E6F1FB" : "var(--ww-surface)",
            transition: "all .15s",
            marginBottom: 16,
            cursor:     "pointer",
          }}
        >
          <input
            id="ww-file-input"
            type="file"
            accept=".log,.txt,.evtx"
            onChange={handleFileInput}
            style={{ display: "none" }}
          />
          <i
            className="ti ti-cloud-upload"
            style={{ fontSize: 34, color: dragOver ? "#378ADD" : "var(--ww-muted)" }}
            aria-hidden="true"
          />
          <div style={{ fontSize: 14, fontWeight: 500, color: "var(--ww-text)", marginTop: 10 }}>
            {uploading ? "Uploading and parsing…" : "Drag a log file here, or click to browse"}
          </div>
          <div style={{ fontSize: 12, color: "var(--ww-muted)", marginTop: 4 }}>
            Supports Apache / Nginx (.log, .txt), Syslog (.log, .txt), Windows Event Logs (.evtx)
          </div>
        </div>

        {/* ── Error banner ──────────────────────────────────────── */}
        {error && (
          <Card style={{ marginBottom: 16, borderColor: "#F0997B", background: "#FAECE7" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <i className="ti ti-alert-circle" style={{ fontSize: 16, color: "#712B13" }} aria-hidden="true" />
              <span style={{ fontSize: 12, color: "#712B13" }}>{error}</span>
            </div>
          </Card>
        )}

        {/* ── Upload result ─────────────────────────────────────── */}
        {result && (
          <Card style={{ marginBottom: 16 }}>
            <CardTitle icon="circle-check">Upload result — {result.filename}</CardTitle>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 14 }}>
              <Metric label="Format"    value={FORMAT_LABEL[result.format] || result.format} />
              <Metric label="Lines"     value={result.total_lines ?? "—"} />
              <Metric label="Parsed"    value={result.parsed      ?? "—"} color="#1D9E75" />
              <Metric label="Flagged"   value={result.flagged     ?? "—"} color={result.flagged > 0 ? "#D85A30" : "var(--ww-text)"} />
            </div>

            {result.sample && result.sample.length > 0 && (
              <>
                <div style={{ fontSize: 11, color: "var(--ww-muted)", marginBottom: 8 }}>
                  Sample entries (first {result.sample.length})
                </div>
                <div style={{ border: "0.5px solid var(--ww-border)", borderRadius: 8, overflow: "hidden" }}>
                  {result.sample.map((s, i) => (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", gap: 10, padding: "7px 12px",
                      borderBottom: i < result.sample.length - 1 ? "0.5px solid var(--ww-border)" : "none",
                      background: s.flagged ? "#FAECE7" : "var(--ww-card)",
                    }}>
                      {s.flagged
                        ? <i className="ti ti-flag-filled"  style={{ fontSize: 12, color: "#D85A30" }} aria-hidden="true" />
                        : <i className="ti ti-circle-check" style={{ fontSize: 12, color: "#1D9E75" }} aria-hidden="true" />}
                      <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--ww-muted)", minWidth: 110 }}>
                        {s.source_ip || "—"}
                      </span>
                      <span style={{ fontSize: 11, color: "var(--ww-text)", flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {s.raw}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </Card>
        )}

        {/* ── Upload history ────────────────────────────────────── */}
        <Card>
          <CardTitle icon="history">Upload history</CardTitle>
          {(!history || history.length === 0) && (
            <p style={{ fontSize: 12, color: "var(--ww-muted)", margin: 0 }}>
              No files uploaded yet this session.
            </p>
          )}
          {(history || []).map((h, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "8px 0", borderBottom: "0.5px solid var(--ww-border)",
            }}>
              <i className="ti ti-file-text" style={{ fontSize: 14, color: "var(--ww-muted)" }} aria-hidden="true" />
              <span style={{ fontSize: 12, color: "var(--ww-text)", fontFamily: "monospace" }}>{h.filename}</span>
              <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 99, background: "var(--ww-surface)", color: "var(--ww-muted)" }}>
                {FORMAT_LABEL[h.format] || h.format}
              </span>
              <span style={{ fontSize: 10, color: "var(--ww-muted)", marginLeft: "auto" }}>
                {h.parsed} parsed
                {h.flagged > 0 && (
                  <span style={{ color: "#D85A30", marginLeft: 6 }}>· {h.flagged} flagged</span>
                )}
              </span>
              <span style={{ fontSize: 10, color: "var(--ww-muted)" }}>
                {new Date(h.uploaded_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          ))}
        </Card>

      </div>
    </>
  );
}

export default UploadLogs;
