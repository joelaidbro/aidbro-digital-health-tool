import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Brand Colors ──────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#060D1F")
NAVY_LIGHT = colors.HexColor("#0F1E38")
ORANGE     = colors.HexColor("#FF6B00")
ORANGE_LT  = colors.HexColor("#FFB347")
WHITE      = colors.white
GRAY       = colors.HexColor("#A0AEC0")
GRAY_LIGHT = colors.HexColor("#E2E8F0")
GREEN      = colors.HexColor("#22C55E")
YELLOW_C   = colors.HexColor("#EAB308")
RED        = colors.HexColor("#EF4444")


def _pillar_color(color_key: str):
    return {"green": GREEN, "yellow": YELLOW_C, "red": RED}.get(color_key, GRAY)


def generate_pdf(
    business_name: str,
    location: str,
    score_data: dict,
    google_data: dict,
    pagespeed_data: dict,
    ai_insights: dict,
) -> bytes:
    """Generate a branded Aidbro Digital Health Report PDF."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Helper styles ─────────────────────────────────────────────────────────
    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    h1 = style("H1", fontSize=22, textColor=WHITE, fontName="Helvetica-Bold",
               spaceAfter=4, leading=26)
    h2 = style("H2", fontSize=14, textColor=ORANGE, fontName="Helvetica-Bold",
               spaceAfter=4, leading=18)
    h3 = style("H3", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold",
               spaceAfter=2, leading=14)
    body = style("Body", fontSize=9, textColor=GRAY, fontName="Helvetica",
                 spaceAfter=3, leading=13)
    body_white = style("BodyW", fontSize=9, textColor=WHITE, fontName="Helvetica",
                       spaceAfter=3, leading=13)
    small = style("Small", fontSize=8, textColor=GRAY, fontName="Helvetica",
                  spaceAfter=2, leading=11)
    caption = style("Caption", fontSize=8, textColor=ORANGE, fontName="Helvetica-Bold",
                    spaceAfter=1)

    W, H = A4
    content_width = W - 30 * mm

    total = score_data.get("total_score", 0)
    grade = score_data.get("grade", "?")
    label = score_data.get("label", "")
    pillars = score_data.get("pillars", {})
    top_fixes = score_data.get("top_fixes", [])
    is_mocked = score_data.get("is_mocked", False)
    date_str = datetime.now().strftime("%d %B %Y")

    # ── HEADER BANNER ─────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("AIDBRO", style("Brand", fontSize=18, textColor=ORANGE,
                                  fontName="Helvetica-Bold")),
        Paragraph(
            f"<b>Digital Health Report</b><br/><font size=8 color='#A0AEC0'>"
            f"Powered by Reals Digital Innovations · {date_str}</font>",
            style("HdrR", fontSize=11, textColor=WHITE,
                  fontName="Helvetica-Bold", alignment=TA_RIGHT)
        )
    ]]
    header_table = Table(header_data, colWidths=[content_width * 0.5, content_width * 0.5])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1), 10),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5 * mm))

    # ── BUSINESS INFO + BIG SCORE ─────────────────────────────────────────────
    score_color = GREEN if total >= 70 else (YELLOW_C if total >= 50 else RED)

    info_col = [
        Paragraph(f"<b>{business_name}</b>", h1),
        Paragraph(f"📍 {location}", style("Loc", fontSize=10, textColor=GRAY,
                                          fontName="Helvetica")),
        Spacer(1, 3 * mm),
        Paragraph(ai_insights.get("greeting", ""), body_white),
        Spacer(1, 2 * mm),
        Paragraph(ai_insights.get("summary", ""), body),
    ]
    if is_mocked:
        info_col.append(Paragraph(
            "⚠️ Demo mode — scores shown are illustrative only.",
            style("Mock", fontSize=8, textColor=YELLOW_C, fontName="Helvetica-Oblique")
        ))

    grade_label_color = score_color

    score_col = [
        Table(
            [[Paragraph(str(total), style("ScoreNum", fontSize=48,
                                          textColor=score_color, fontName="Helvetica-Bold",
                                          alignment=TA_CENTER))]],
            colWidths=[50 * mm],
            rowHeights=[55 * mm]
        ),
        Paragraph(f"<b>Grade: {grade}</b>", style("Grade", fontSize=14,
                                                    textColor=score_color,
                                                    fontName="Helvetica-Bold",
                                                    alignment=TA_CENTER)),
        Paragraph(label, style("Label", fontSize=10, textColor=GRAY,
                               fontName="Helvetica", alignment=TA_CENTER)),
    ]

    top_table = Table(
        [[info_col, score_col]],
        colWidths=[content_width * 0.68, content_width * 0.32]
    )
    top_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 5 * mm))

    # ── PILLAR SCORES BAR ─────────────────────────────────────────────────────
    story.append(Paragraph("PILLAR SCORES", h2))
    story.append(HRFlowable(width=content_width, color=ORANGE, thickness=0.5))
    story.append(Spacer(1, 2 * mm))

    pillar_rows = []
    for key, p in pillars.items():
        bar_filled = round((p["score"] / p["max"]) * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        pillar_rows.append([
            Paragraph(f"{p['icon']} {p['name']}", style(
                "PI", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold")),
            Paragraph(bar, style("Bar", fontSize=7, textColor=_pillar_color(p["color"]),
                                 fontName="Courier")),
            Paragraph(f"<b>{p['score']}/{p['max']}</b>", style(
                "PScore", fontSize=10, textColor=_pillar_color(p["color"]),
                fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ])

    pillar_table = Table(
        pillar_rows,
        colWidths=[content_width * 0.30, content_width * 0.50, content_width * 0.20]
    )
    pillar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_LIGHT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [NAVY_LIGHT, NAVY]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 10),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
    ]))
    story.append(pillar_table)
    story.append(Spacer(1, 5 * mm))

    # ── DETAILED CHECKS ───────────────────────────────────────────────────────
    story.append(Paragraph("DETAILED ANALYSIS", h2))
    story.append(HRFlowable(width=content_width, color=ORANGE, thickness=0.5))
    story.append(Spacer(1, 2 * mm))

    for key, p in pillars.items():
        check_rows = [
            [
                Paragraph("✓" if c["passed"] else "✗", style(
                    "Tick", fontSize=10,
                    textColor=GREEN if c["passed"] else RED,
                    fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(c["check"], style("CkName", fontSize=8,
                                            textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(c.get("value", ""), style("CkVal", fontSize=8,
                                                     textColor=ORANGE_LT,
                                                     fontName="Helvetica")),
                Paragraph(c["message"], body),
                Paragraph(f"+{c['points_earned']}/{c['points_max']}", style(
                    "Pts", fontSize=8,
                    textColor=GREEN if c["passed"] else RED,
                    fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            ]
            for c in p["checks"]
        ]

        section = KeepTogether([
            Paragraph(f"{p['icon']}  {p['name'].upper()}", h3),
            Table(
                check_rows,
                colWidths=[
                    content_width * 0.04,
                    content_width * 0.23,
                    content_width * 0.12,
                    content_width * 0.48,
                    content_width * 0.13,
                ]
            )
        ])

        tbl = section.flowables[-1]
        tbl.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [NAVY, NAVY_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 6),
        ]))

        story.append(section)
        story.append(Spacer(1, 3 * mm))

    # ── TOP PRIORITY FIXES ────────────────────────────────────────────────────
    if top_fixes:
        story.append(Paragraph("🎯  TOP PRIORITY FIXES", h2))
        story.append(HRFlowable(width=content_width, color=ORANGE, thickness=0.5))
        story.append(Spacer(1, 2 * mm))

        fix_rows = [
            [
                Paragraph(f"#{i+1}", style("FN", fontSize=12, textColor=ORANGE,
                                            fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"<b>{f['check']}</b><br/>{f['fix']}",
                          style("FT", fontSize=9, textColor=WHITE,
                                fontName="Helvetica", leading=13)),
                Paragraph(f"Aidbro Service:<br/><b>{f['service']}</b>",
                          style("FS", fontSize=8, textColor=ORANGE_LT,
                                fontName="Helvetica", alignment=TA_RIGHT, leading=12)),
            ]
            for i, f in enumerate(top_fixes[:3])
        ]
        fix_table = Table(
            fix_rows,
            colWidths=[content_width * 0.06, content_width * 0.65, content_width * 0.29]
        )
        fix_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY_LIGHT),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [NAVY, NAVY_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 8),
        ]))
        story.append(fix_table)
        story.append(Spacer(1, 5 * mm))

    # ── AI INSIGHT + CTA ──────────────────────────────────────────────────────
    cta_data = [[
        Paragraph(
            f"<b>{ai_insights.get('insight', '')}</b><br/><br/>"
            f"<font color='#FF6B00'>{ai_insights.get('cta', '')}</font>",
            style("CTAText", fontSize=10, textColor=WHITE,
                  fontName="Helvetica", leading=16)
        )
    ]]
    cta_table = Table(cta_data, colWidths=[content_width])
    cta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 14),
        ("LINEABOVE", (0, 0), (-1, 0), 2, ORANGE),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(cta_table)
    story.append(Spacer(1, 4 * mm))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    footer_data = [[
        Paragraph("📞 +91 8589999362", small),
        Paragraph("✉️  Info@realsdigitalinnovations.com", small),
        Paragraph("🌐 realsdigitalinnovations.com", small),
        Paragraph("📍 Kannur, Kerala", small),
    ]]
    footer_table = Table(footer_data,
                         colWidths=[content_width / 4] * 4)
    footer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(footer_table)

    # Build PDF
    def _bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg)
    return buffer.getvalue()