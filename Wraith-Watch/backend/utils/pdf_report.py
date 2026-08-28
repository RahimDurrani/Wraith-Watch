from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT

# ── Severity colour map for the PDF ───────────────────────────────────────────
SEV_COLORS = {
    "critical": colors.HexColor("#D85A30"),
    "high": colors.HexColor("#BA7517"),
    "medium": colors.HexColor("#378ADD"),
    "low": colors.HexColor("#639922"),
    "info": colors.HexColor("#888780"),
}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="WWTitle", fontName="Helvetica-Bold", fontSize=20,
        textColor=colors.HexColor("#1A1A18"), spaceAfter=4, leading=24,
    ))
    styles.add(ParagraphStyle(
        name="WWSubtitle", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#73726C"), spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="WWSection", fontName="Helvetica-Bold", fontSize=13,
        textColor=colors.HexColor("#1A1A18"), spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="WWBody", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#2C2C2A"), leading=15, spaceAfter=6,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="WWLabel", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.HexColor("#73726C"),
    ))
    styles.add(ParagraphStyle(
        name="WWMono", fontName="Courier", fontSize=8,
        textColor=colors.HexColor("#444441"), leading=12,
    ))
    styles.add(ParagraphStyle(
        name="WWNote", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#2C2C2A"), leading=13, spaceAfter=2,
    ))
    return styles


def generate_incident_pdf(incident, alerts: list) -> bytes:
    """
    Build a forensic PDF report for an incident.

    Args:
        incident - Incident model instance (has .to_dict())
        alerts   - list of Alert model instances linked to this incident

    Returns:
        PDF file as bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"Incident Report INC-{incident.id:03d}",
    )
    s = _styles()
    story = []
    data = incident.to_dict()

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("WraithWatch — Incident Report", s["WWTitle"]))
    story.append(Paragraph(
        f"Generated {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')} · "
        f"DFIR SIEM Platform", s["WWSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#D3D1C7")))
    story.append(Spacer(1, 10))

    # ── Incident summary ──────────────────────────────────────────────────────
    story.append(Paragraph(f"INC-{incident.id:03d} — {incident.title}", s["WWSection"]))

    sev_color = SEV_COLORS.get(incident.severity, colors.grey)
    summary_rows = [
        [Paragraph("Severity", s["WWLabel"]),
         Paragraph(f'<font color="{sev_color.hexval()}"><b>{incident.severity.upper()}</b></font>', s["WWBody"])],
        [Paragraph("Status", s["WWLabel"]),      Paragraph(incident.status.replace("_", " ").title(), s["WWBody"])],
        [Paragraph("Assigned to", s["WWLabel"]), Paragraph(incident.analyst or "Unassigned", s["WWBody"])],
        [Paragraph("Linked alerts", s["WWLabel"]), Paragraph(str(len(alerts)), s["WWBody"])],
        [Paragraph("Created", s["WWLabel"]),     Paragraph(data.get("created_at", "—"), s["WWBody"])],
    ]
    t = Table(summary_rows, colWidths=[35 * mm, 130 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#E8E6DF")),
    ]))
    story.append(t)

    # ── Description ───────────────────────────────────────────────────────────
    if incident.description:
        story.append(Paragraph("Description", s["WWSection"]))
        story.append(Paragraph(incident.description, s["WWBody"]))

    # ── Linked alerts ─────────────────────────────────────────────────────────
    story.append(Paragraph("Linked alerts", s["WWSection"]))
    if alerts:
        alert_rows = [[
            Paragraph("<b>Severity</b>", s["WWNote"]),
            Paragraph("<b>Alert</b>", s["WWNote"]),
            Paragraph("<b>Source IP</b>", s["WWNote"]),
            Paragraph("<b>Abuse</b>", s["WWNote"]),
        ]]
        for a in alerts:
            ac = SEV_COLORS.get(a.severity, colors.grey)
            alert_rows.append([
                Paragraph(f'<font color="{ac.hexval()}">{a.severity}</font>', s["WWNote"]),
                Paragraph(a.title, s["WWNote"]),
                Paragraph(a.source_ip or "—", s["WWMono"]),
                Paragraph(str(a.abuse_score) if a.abuse_score is not None else "—", s["WWNote"]),
            ])
        at = Table(alert_rows, colWidths=[22 * mm, 90 * mm, 34 * mm, 18 * mm])
        at.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F4F0")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E8E6DF")),
        ]))
        story.append(at)
    else:
        story.append(Paragraph("No alerts linked to this incident.", s["WWBody"]))

    # ── Analyst notes ─────────────────────────────────────────────────────────
    story.append(Paragraph("Analyst notes", s["WWSection"]))
    notes = data.get("notes", [])
    if notes:
        for n in notes:
            story.append(Paragraph(
                f'<b>{n["author"]}</b> · {n.get("created_at", "")}', s["WWLabel"]))
            story.append(Paragraph(n["content"], s["WWNote"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No notes recorded.", s["WWBody"]))

    # ── Audit trail ───────────────────────────────────────────────────────────
    story.append(Paragraph("Audit trail", s["WWSection"]))
    audit = data.get("audit", [])
    if audit:
        audit_rows = [[
            Paragraph("<b>Time</b>", s["WWNote"]),
            Paragraph("<b>Action</b>", s["WWNote"]),
            Paragraph("<b>User</b>", s["WWNote"]),
        ]]
        for a in audit:
            audit_rows.append([
                Paragraph(a.get("time", ""), s["WWNote"]),
                Paragraph(a.get("action", ""), s["WWNote"]),
                Paragraph(a.get("user", ""), s["WWNote"]),
            ])
        aud = Table(audit_rows, colWidths=[20 * mm, 110 * mm, 34 * mm])
        aud.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F4F0")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E8E6DF")),
        ]))
        story.append(aud)
    else:
        story.append(Paragraph("No audit entries.", s["WWBody"]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#D3D1C7")))
    story.append(Paragraph(
        "This report was generated automatically by WraithWatch for forensic and "
        "incident-response purposes. All timestamps are in UTC.", s["WWSubtitle"]))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
