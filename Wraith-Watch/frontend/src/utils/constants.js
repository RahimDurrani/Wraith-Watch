// src/utils/constants.js
// ─────────────────────────────────────────────────────────
// Global constants — colours, status maps, API base URL.
// Change API here if your Flask port changes.
// ─────────────────────────────────────────────────────────

export const API = "http://localhost:5000/api";

export const SEV_CONFIG = {
  critical: { bg: "#FAECE7", text: "#712B13", border: "#F0997B", dot: "#D85A30" },
  high:     { bg: "#FAEEDA", text: "#633806", border: "#EF9F27", dot: "#BA7517" },
  medium:   { bg: "#E6F1FB", text: "#0C447C", border: "#85B7EB", dot: "#378ADD" },
  low:      { bg: "#EAF3DE", text: "#27500A", border: "#97C459", dot: "#639922" },
  info:     { bg: "#F1EFE8", text: "#444441", border: "#B4B2A9", dot: "#888780" },
};

export const STATUS_CONFIG = {
  open:          { bg: "#FAECE7", text: "#712B13" },
  in_progress:   { bg: "#FAEEDA", text: "#633806" },
  false_positive:{ bg: "#F1EFE8", text: "#444441" },
  closed:        { bg: "#EAF3DE", text: "#27500A" },
  new:           { bg: "#FAEEDA", text: "#633806" },
  triaged:       { bg: "#E6F1FB", text: "#0C447C" },
  investigating: { bg: "#EEEDFE", text: "#3C3489" },
};

export const SRC_STATUS = {
  active: { dot: "#1D9E75", badge_bg: "#EAF3DE", badge_text: "#27500A" },
  stale:  { dot: "#BA7517", badge_bg: "#FAEEDA", badge_text: "#633806" },
  silent: { dot: "#D85A30", badge_bg: "#FAECE7", badge_text: "#712B13" },
};

export const FLAG_COLORS = {
  critical: { bg: "#FAECE7", text: "#712B13", border: "#F0997B", dot: "#D85A30" },
  high:     { bg: "#FAEEDA", text: "#633806", border: "#EF9F27", dot: "#BA7517" },
  medium:   { bg: "#E6F1FB", text: "#0C447C", border: "#85B7EB", dot: "#378ADD" },
  info:     { bg: "transparent", text: "var(--ww-muted)", border: "transparent", dot: "#B4B2A9" },
};

export const LOG_TYPE_COLORS = {
  apache: { bg: "#EAF3DE", text: "#27500A" },
  syslog: { bg: "#E6F1FB", text: "#0C447C" },
  evtx:   { bg: "#EEEDFE", text: "#3C3489" },
};
