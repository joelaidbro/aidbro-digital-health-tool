"""
Aidbro Digital Health Report — PDF Generator v3
=================================================
Fixed: KeepTogether.flowables AttributeError
Fixed: Table style applied before KeepTogether wrapping
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Brand palette ─────────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#060D1F")
NAVY_MID    = colors.HexColor("#0B1628")
NAVY_LIGHT  = colors.HexColor("#0F1E38")
ORANGE      = colors.HexColor("#FF6B00")
ORANGE_LT   = colors.HexColor("#FF8C3A")
WHITE       = colors.white
GRAY        = colors.HexColor("#A0AEC0")
GRAY_DIM    = colors.HexColor("#4A5568")
GREEN       = colors.HexColor("#22C55E")
YELLOW      = colors.HexColor("#EAB308")
RED         = colors.HexColor("#EF4444")
RED_DIM     = colors.HexColor("#2B0E0E")
ORANGE_DIM  = colors.HexColor("#2A1800")

W, H   = A4
MARGIN = 14 * mm
CW     = W - 2 * MARGIN


def _c(color_key):
    return {"green": GREEN, "yellow": YELLOW, "red": RED}.get(color_key, GRAY)


def S(name, **kw):
    return ParagraphStyle(name, **kw)


def _bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#1A0900"))
    canvas.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)
    canvas.restoreState()


def _hr(color=ORANGE, thickness=0.5):
    return HRFlowable(width=CW, color=color, thickness=thickness, spaceAfter=3)


def _section(title, st):
    return [Paragraph(title, st["h2"]), _hr(), Spacer(1, 3 * mm)]


def _styled_table(data, col_widths, style_cmds):
    """Build and style a table — style is applied BEFORE any KeepTogether wrapping."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style_cmds))
    return t


def generate_pdf(
    business_name, location, score_data, google_data,
    pagespeed_data, ai_insights, seo_data=None,
    competitor_data=None, keyword_data=None,
):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
    )

    st = {
        "brand":  S("brand", fontSize=22, textColor=ORANGE,     fontName="Helvetica-Bold"),
        "h1":     S("h1",    fontSize=20, textColor=WHITE,      fontName="Helvetica-Bold",  spaceAfter=4,  leading=24),
        "h2":     S("h2",    fontSize=12, textColor=ORANGE,     fontName="Helvetica-Bold",  spaceAfter=3,  leading=16),
        "h3":     S("h3",    fontSize=10, textColor=WHITE,      fontName="Helvetica-Bold",  spaceAfter=2,  leading=14),
        "body":   S("body",  fontSize=8.5,textColor=GRAY,       fontName="Helvetica",       spaceAfter=3,  leading=13),
        "small":  S("small", fontSize=7.5,textColor=GRAY_DIM,   fontName="Helvetica",       spaceAfter=2,  leading=11),
        "small_o":S("smallo",fontSize=7.5,textColor=ORANGE_LT,  fontName="Helvetica",       spaceAfter=2,  leading=11),
    }

    story = []
    date  = datetime.now().strftime("%d %B %Y")

    total   = score_data.get("total_score", 0)
    grade   = score_data.get("grade", "?")
    label   = score_data.get("label", "")
    pillars = score_data.get("pillars", {})
    fixes   = score_data.get("top_fixes", [])
    sc      = GREEN if total >= 70 else (YELLOW if total >= 50 else RED)

    # ── HEADER ────────────────────────────────────────────────────────────────
    hdr = _styled_table(
        [[Paragraph("AIDBRO", st["brand"]),
          Paragraph(
              f"<b>Digital Health Report</b><br/>"
              f"<font size=7 color='#A0AEC0'>Reals Digital Innovations · {date}</font>",
              S("hr", fontSize=10, textColor=WHITE, fontName="Helvetica-Bold",
                alignment=TA_RIGHT, leading=14)
          )]],
        [CW * 0.5, CW * 0.5],
        [("BACKGROUND",(0,0),(-1,-1),NAVY_LIGHT),
         ("TOPPADDING",(0,0),(-1,-1),10),
         ("BOTTOMPADDING",(0,0),(-1,-1),10),
         ("LEFTPADDING",(0,0),(0,-1),12),
         ("RIGHTPADDING",(-1,0),(-1,-1),12),
         ("LINEBELOW",(0,0),(-1,-1),1.5,ORANGE)],
    )
    story.append(hdr)
    story.append(Spacer(1, 5 * mm))

    # ── BUSINESS INFO + SCORE ─────────────────────────────────────────────────
    info_items = [
        Paragraph(f"<b>{business_name}</b>", st["h1"]),
        Paragraph(f"📍 {google_data.get('address', location)}",
                  S("loc", fontSize=9, textColor=GRAY, fontName="Helvetica")),
        Spacer(1, 2 * mm),
    ]
    for icon, key in [("📞 ", "phone"), ("🌐 ", "website")]:
        val = google_data.get(key, "")
        if val:
            info_items.append(Paragraph(
                icon + val.replace("https://","").replace("http://",""),
                S(f"i{key}", fontSize=9, textColor=GRAY if key=="phone" else ORANGE_LT,
                  fontName="Helvetica")
            ))
    if score_data.get("category"):
        info_items.append(Paragraph(f"🏢 {score_data['category']}",
                  S("cat", fontSize=9, textColor=GRAY, fontName="Helvetica")))
    info_items += [
        Spacer(1, 3*mm),
        Paragraph(ai_insights.get("greeting",""),
                  S("gr", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold", leading=13)),
        Spacer(1, 2*mm),
        Paragraph(ai_insights.get("summary",""), st["body"]),
    ]

    score_col = _styled_table(
        [[Paragraph(str(total), S("sn", fontSize=12, textColor=sc,
                                   fontName="Helvetica-Bold", alignment=TA_CENTER))],
         [Paragraph(f"<b>Grade: {grade}</b>",
                    S("g2", fontSize=12, textColor=sc,
                      fontName="Helvetica-Bold", alignment=TA_CENTER))],
         [Paragraph(label, S("lb", fontSize=9, textColor=GRAY,
                              fontName="Helvetica", alignment=TA_CENTER))],
         [Paragraph("/ 100", S("d", fontSize=9, textColor=GRAY_DIM,
                                fontName="Helvetica", alignment=TA_CENTER))]],
        [CW * 0.28],
        [("BACKGROUND",(0,0),(-1,-1),NAVY_MID),
         ("TOPPADDING",(0,0),(-1,-1),4),
         ("BOTTOMPADDING",(0,0),(-1,-1),4),
         ("ALIGN",(0,0),(-1,-1),"CENTER"),
         ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
         ("LINEBEFORE",(0,0),(0,-1),1,ORANGE)],
    )

    hero = _styled_table(
        [[info_items, score_col]],
        [CW * 0.70, CW * 0.30],
        [("BACKGROUND",(0,0),(-1,-1),NAVY_MID),
         ("VALIGN",(0,0),(-1,-1),"TOP"),
         ("TOPPADDING",(0,0),(0,-1),10),
         ("BOTTOMPADDING",(0,0),(0,-1),10),
         ("LEFTPADDING",(0,0),(0,-1),12),
         ("RIGHTPADDING",(-1,0),(-1,-1),0),
         ("LINEBELOW",(0,0),(-1,-1),1,ORANGE)],
    )
    story.append(hero)
    story.append(Spacer(1, 5 * mm))

    # ── PILLAR BARS ───────────────────────────────────────────────────────────
    story.extend(_section("PILLAR SCORES", st))

    bar_rows = []
    for p in pillars.values():
        pct      = p.get("percent", 0)
        bar_fill = round(pct / 5)
        bar_str  = "█" * bar_fill + "░" * (20 - bar_fill)
        color    = _c(p.get("color", "red"))
        bar_rows.append([
            Paragraph(f"{p['icon']}  {p['name']}", st["h3"]),
            Paragraph(bar_str, S("bar", fontSize=6.5, textColor=color, fontName="Courier")),
            Paragraph(f"<b>{p['score']}/{p['max']}</b>",
                      S("ps", fontSize=10, textColor=color,
                        fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ])

    story.append(_styled_table(
        bar_rows,
        [CW*0.30, CW*0.52, CW*0.18],
        [("ROWBACKGROUNDS",(0,0),(-1,-1),[NAVY_LIGHT, NAVY_MID]),
         ("TOPPADDING",(0,0),(-1,-1),7),
         ("BOTTOMPADDING",(0,0),(-1,-1),7),
         ("LEFTPADDING",(0,0),(-1,-1),10),
         ("RIGHTPADDING",(-1,0),(-1,-1),10),
         ("VALIGN",(0,0),(-1,-1),"MIDDLE")],
    ))
    story.append(Spacer(1, 5 * mm))

    # ── DETAILED CHECKS ───────────────────────────────────────────────────────
    story.extend(_section("DETAILED ANALYSIS", st))

    for p in pillars.values():
        check_rows = []
        for c in p.get("checks", []):
            if c.get("skipped") and c.get("points_max", 0) == 0:
                continue
            passed = c.get("passed", False)

            # Build fix paragraph if needed
            body_content = c.get("message","")
            if not passed and c.get("fix"):
                body_content += f"<br/><font color='#FF8C3A'>→ {c['fix']}</font>"

            check_rows.append([
                Paragraph("✓" if passed else "✗",
                          S("tk", fontSize=10,
                            textColor=GREEN if passed else RED,
                            fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(c.get("check",""),
                          S("cn", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(str(c.get("value","") or ""),
                          S("cv", fontSize=7.5, textColor=ORANGE_LT, fontName="Helvetica")),
                Paragraph(body_content, st["body"]),
                Paragraph(f"+{c.get('points_earned',0)}/{c.get('points_max',0)}",
                          S("pts", fontSize=8,
                            textColor=GREEN if passed else RED,
                            fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            ])

        if not check_rows:
            continue

        # ── FIX: Build table first, style it, THEN wrap in KeepTogether ──────
        check_table = _styled_table(
            check_rows,
            [CW*0.04, CW*0.22, CW*0.11, CW*0.50, CW*0.13],
            [("ROWBACKGROUNDS",(0,0),(-1,-1),[NAVY_MID, NAVY_LIGHT]),
             ("TOPPADDING",(0,0),(-1,-1),4),
             ("BOTTOMPADDING",(0,0),(-1,-1),4),
             ("LEFTPADDING",(0,0),(-1,-1),6),
             ("RIGHTPADDING",(-1,0),(-1,-1),6),
             ("VALIGN",(0,0),(-1,-1),"TOP")],
        )

        pillar_header = Paragraph(
            f"{p['icon']}  {p['name'].upper()}",
            S("ph", fontSize=9, textColor=_c(p.get("color","red")),
              fontName="Helvetica-Bold", spaceAfter=3)
        )

        # KeepTogether takes pre-built flowables — no .flowables access needed
        section_block = KeepTogether([pillar_header, check_table])
        story.append(section_block)
        story.append(Spacer(1, 3 * mm))

    # ── SEO AUDIT SUMMARY ─────────────────────────────────────────────────────
    if seo_data and not seo_data.get("error"):
        story.append(Spacer(1, 2*mm))
        story.extend(_section("SEO SITE AUDIT", st))

        summary = seo_data.get("summary", {})
        site    = seo_data.get("site_level", {})
        issues  = seo_data.get("issues", [])
        recs    = seo_data.get("recommendations", [])

        # Stat grid
        stat_pairs = [
            ("robots.txt",    "✓ Found"   if site.get("has_robots_txt")    else "✗ Missing",  site.get("has_robots_txt")),
            ("sitemap.xml",   "✓ Found"   if site.get("has_sitemap")       else "✗ Missing",  site.get("has_sitemap")),
            ("HTTPS",         "✓ Secure"  if site.get("all_pages_https")   else "✗ Insecure", site.get("all_pages_https")),
            ("Schema Markup", "✓ Found"   if summary.get("has_schema")     else "✗ Missing",  summary.get("has_schema")),
            ("Open Graph",    "✓ Complete"if summary.get("og_complete")    else "✗ Incomplete",summary.get("og_complete")),
            ("Word Count",    f"{summary.get('homepage_word_count',0)} words",
                              (summary.get("homepage_word_count",0) >= 300)),
            ("Alt Text",
                              f"{summary.get('images_missing_alt',0)} missing" if summary.get("images_missing_alt",0) > 0 else "✓ All OK",
                              summary.get("images_missing_alt",0) == 0),
            ("Load Time",
                              f"{seo_data.get('pages',[{}])[0].get('load_time_ms','?')}ms" if seo_data.get("pages") else "N/A",
                              True),
        ]

        # 2 rows × 4 cols
        seo_grid_rows = []
        for i in range(0, 8, 4):
            row = []
            for label, value, ok in stat_pairs[i:i+4]:
                cell = _styled_table(
                    [[Paragraph(label, S("sl",fontSize=7.5,textColor=GRAY,
                                         fontName="Helvetica",alignment=TA_CENTER))],
                     [Paragraph(value, S("sv",fontSize=8.5,
                                          textColor=GREEN if ok else RED,
                                          fontName="Helvetica-Bold",alignment=TA_CENTER))]],
                    [(CW/4) - 3*mm],
                    [("BACKGROUND",(0,0),(-1,-1),NAVY_LIGHT),
                     ("TOPPADDING",(0,0),(-1,-1),6),
                     ("BOTTOMPADDING",(0,0),(-1,-1),6),
                     ("ALIGN",(0,0),(-1,-1),"CENTER")],
                )
                row.append(cell)
            seo_grid_rows.append(row)

        seo_grid = _styled_table(
            seo_grid_rows,
            [CW/4]*4,
            [("BACKGROUND",(0,0),(-1,-1),NAVY_LIGHT),
             ("GRID",(0,0),(-1,-1),0.5,NAVY_MID),
             ("TOPPADDING",(0,0),(-1,-1),6),
             ("BOTTOMPADDING",(0,0),(-1,-1),6),
             ("LEFTPADDING",(0,0),(-1,-1),4),
             ("RIGHTPADDING",(-1,0),(-1,-1),4)],
        )
        story.append(seo_grid)
        story.append(Spacer(1, 4*mm))

        # Google search preview
        hp = seo_data.get("pages", [{}])[0] if seo_data.get("pages") else {}
        if hp.get("title"):
            story.append(Paragraph("Google Search Preview", st["h3"]))
            story.append(Spacer(1, 2*mm))
            preview_rows = [
                [Paragraph(seo_data.get("url","").replace("https://","").replace("http://",""),
                           S("pu",fontSize=8,textColor=GREEN,fontName="Helvetica"))],
                [Paragraph(hp.get("title",""),
                           S("pt",fontSize=11,textColor=colors.HexColor("#8ab4f8"),
                             fontName="Helvetica-Bold",leading=14))],
            ]
            if hp.get("meta_description"):
                preview_rows.append([
                    Paragraph(hp["meta_description"][:160],
                              S("pd",fontSize=8,textColor=GRAY,fontName="Helvetica",leading=12))
                ])
            story.append(_styled_table(
                preview_rows, [CW],
                [("BACKGROUND",(0,0),(-1,-1),NAVY_MID),
                 ("TOPPADDING",(0,0),(-1,-1),6),
                 ("BOTTOMPADDING",(0,0),(-1,-1),6),
                 ("LEFTPADDING",(0,0),(-1,-1),10),
                 ("RIGHTPADDING",(-1,0),(-1,-1),10),
                 ("LINEABOVE",(0,0),(-1,0),1,ORANGE_LT)],
            ))
            story.append(Spacer(1, 4*mm))

        # Critical issues
        crits = [i for i in issues if i["severity"]=="critical"][:4]
        if crits:
            story.append(Paragraph("Critical SEO Issues", st["h3"]))
            story.append(Spacer(1, 2*mm))
            story.append(_styled_table(
                [[Paragraph("🔴",S("ii",fontSize=9,fontName="Helvetica")),
                  Paragraph(i["issue"],S("it",fontSize=8,textColor=RED,fontName="Helvetica-Bold")),
                  Paragraph(i["fix"],st["body"])] for i in crits],
                [CW*0.04, CW*0.34, CW*0.62],
                [("BACKGROUND",(0,0),(-1,-1),RED_DIM),
                 ("TOPPADDING",(0,0),(-1,-1),5),
                 ("BOTTOMPADDING",(0,0),(-1,-1),5),
                 ("LEFTPADDING",(0,0),(-1,-1),7),
                 ("RIGHTPADDING",(-1,0),(-1,-1),7),
                 ("VALIGN",(0,0),(-1,-1),"TOP"),
                 ("LINEBELOW",(0,0),(-1,-2),0.3,NAVY_MID)],
            ))
            story.append(Spacer(1, 4*mm))

        # AI Recommendations
        if recs:
            story.append(Paragraph("AI SEO Recommendations", st["h3"]))
            story.append(Spacer(1, 2*mm))
            story.append(_styled_table(
                [[Paragraph(str(r["priority"]),
                            S("rn",fontSize=11,textColor=ORANGE,
                              fontName="Helvetica-Bold",alignment=TA_CENTER)),
                  Paragraph(f"<b>{r['title']}</b><br/>"
                            f"<font color='#A0AEC0'>{r['problem']}</font>",
                            S("rb",fontSize=8,textColor=WHITE,
                              fontName="Helvetica",leading=13)),
                  Paragraph(f"→ {r['fix']}",
                            S("rf",fontSize=8,textColor=GRAY,
                              fontName="Helvetica",leading=12)),
                  Paragraph(r.get("impact",""),
                            S("ri",fontSize=8,
                              textColor=RED if r.get("impact")=="High"
                                        else YELLOW if r.get("impact")=="Medium"
                                        else GREEN,
                              fontName="Helvetica-Bold",alignment=TA_CENTER))]
                 for r in recs[:3]],
                [CW*0.05, CW*0.37, CW*0.47, CW*0.11],
                [("ROWBACKGROUNDS",(0,0),(-1,-1),[NAVY_LIGHT, NAVY_MID]),
                 ("TOPPADDING",(0,0),(-1,-1),7),
                 ("BOTTOMPADDING",(0,0),(-1,-1),7),
                 ("LEFTPADDING",(0,0),(-1,-1),8),
                 ("RIGHTPADDING",(-1,0),(-1,-1),8),
                 ("VALIGN",(0,0),(-1,-1),"TOP")],
            ))
            story.append(Spacer(1, 3*mm))

    # ── COMPETITOR ANALYSIS ───────────────────────────────────────────────────
    if competitor_data and competitor_data.get("competitors"):
        story.append(Spacer(1, 2*mm))
        story.extend(_section("COMPETITOR ANALYSIS", st))

        target      = competitor_data.get("target", {})
        competitors = competitor_data.get("competitors", [])[:4]
        gaps        = competitor_data.get("gaps", [])
        ai_summ     = competitor_data.get("ai_summary","")

        if ai_summ:
            story.append(Paragraph(ai_summ, st["body"]))
            story.append(Spacer(1, 3*mm))

        # Matrix header
        header_row = [Paragraph("", st["small"]),
                      Paragraph("<b>YOU</b>",
                                S("you",fontSize=8,textColor=ORANGE,
                                  fontName="Helvetica-Bold",alignment=TA_CENTER))]
        for c in competitors:
            header_row.append(Paragraph(
                c["name"][:16]+("…" if len(c["name"])>16 else ""),
                S("ch",fontSize=7,textColor=GRAY,fontName="Helvetica",alignment=TA_CENTER)
            ))
        while len(header_row) < 6:
            header_row.append(Paragraph("—",st["small"]))

        rows = [header_row]

        for label_str, key, is_bool in [
            ("⭐ Rating","rating",False),
            ("💬 Reviews","review_count",False),
            ("🌐 Website","has_website",True),
            ("📸 Photos","photos_count",False),
            ("✅ Profile %","profile_completeness",False),
        ]:
            target_val = target.get(key, 0)
            row = [Paragraph(label_str,
                             S("dl",fontSize=8,textColor=GRAY,fontName="Helvetica"))]

            avg = (sum(c.get(key,0) for c in competitors)/len(competitors)
                   if competitors else 0)

            if is_bool:
                display = "Yes" if target_val else "No"
                wins    = bool(target_val)
            else:
                display = str(target_val)
                wins    = target_val >= avg

            row.append(Paragraph(f"<b>{display}</b>",
                                  S("yv",fontSize=9,
                                    textColor=GREEN if wins else RED,
                                    fontName="Helvetica-Bold",alignment=TA_CENTER)))

            for comp in competitors:
                val = comp.get(key,0)
                if is_bool:
                    disp   = "Yes" if val else "No"
                    better = val and not wins
                else:
                    disp   = str(val)
                    better = isinstance(val,(int,float)) and val > target_val
                row.append(Paragraph(disp,
                                     S("cv2",fontSize=8,
                                       textColor=RED if better else GRAY_DIM,
                                       fontName="Helvetica",alignment=TA_CENTER)))

            while len(row) < 6:
                row.append(Paragraph("—",st["small"]))
            rows.append(row)

        n_c   = min(len(competitors),4)
        col_w = [CW*0.18, CW*0.12] + [CW*0.70/max(n_c,1)]*n_c
        col_w = col_w[:2+n_c]

        story.append(_styled_table(
            rows, col_w,
            [("BACKGROUND",(0,0),(-1,0),NAVY_MID),
             ("ROWBACKGROUNDS",(0,1),(-1,-1),[NAVY_LIGHT,NAVY_MID]),
             ("TOPPADDING",(0,0),(-1,-1),6),
             ("BOTTOMPADDING",(0,0),(-1,-1),6),
             ("LEFTPADDING",(0,0),(-1,-1),6),
             ("RIGHTPADDING",(-1,0),(-1,-1),6),
             ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
             ("LINEBELOW",(0,0),(-1,0),1,ORANGE)],
        ))
        story.append(Spacer(1, 3*mm))

        # Gaps
        if gaps:
            story.append(Paragraph("Key Competitive Gaps", st["h3"]))
            story.append(Spacer(1, 2*mm))
            story.append(_styled_table(
                [[Paragraph("🔴" if g["severity"]=="critical" else "🟡",
                            S("gi",fontSize=9,fontName="Helvetica")),
                  Paragraph(f"<b>{g['dimension']}</b><br/>{g['message']}",
                            S("gm",fontSize=8,textColor=WHITE,fontName="Helvetica",leading=13)),
                  Paragraph(g["action"],
                            S("ga",fontSize=8,textColor=ORANGE_LT,
                              fontName="Helvetica",leading=12))]
                 for g in gaps[:3]],
                [CW*0.04, CW*0.46, CW*0.50],
                [("ROWBACKGROUNDS",(0,0),(-1,-1),[NAVY_LIGHT,NAVY_MID]),
                 ("TOPPADDING",(0,0),(-1,-1),6),
                 ("BOTTOMPADDING",(0,0),(-1,-1),6),
                 ("LEFTPADDING",(0,0),(-1,-1),8),
                 ("RIGHTPADDING",(-1,0),(-1,-1),8),
                 ("VALIGN",(0,0),(-1,-1),"TOP")],
            ))
            story.append(Spacer(1, 3*mm))

    # ── KEYWORD STRATEGY ──────────────────────────────────────────────────────
    if keyword_data and keyword_data.get("missing_keywords"):
        story.append(Spacer(1, 2*mm))
        story.extend(_section("KEYWORD STRATEGY GAPS", st))

        if keyword_data.get("ai_analysis"):
            story.append(Paragraph(keyword_data["ai_analysis"], st["body"]))
            story.append(Spacer(1, 3*mm))

        if keyword_data.get("disclaimer"):
            story.append(Paragraph(
                keyword_data["disclaimer"],
                S("disc",fontSize=7.5,textColor=YELLOW,
                  fontName="Helvetica-Oblique",leading=11)
            ))
            story.append(Spacer(1, 3*mm))

        missing = keyword_data.get("missing_keywords",[])[:8]
        if missing:
            story.append(_styled_table(
                [[Paragraph(f"✗  {kw['keyword']}  — competitors targeting this",
                            S("kwi",fontSize=8,textColor=RED,fontName="Helvetica",leading=13))]
                 for kw in missing],
                [CW],
                [("ROWBACKGROUNDS",(0,0),(-1,-1),[NAVY_LIGHT,NAVY_MID]),
                 ("TOPPADDING",(0,0),(-1,-1),5),
                 ("BOTTOMPADDING",(0,0),(-1,-1),5),
                 ("LEFTPADDING",(0,0),(-1,-1),10),
                 ("RIGHTPADDING",(-1,0),(-1,-1),10)],
            ))
            story.append(Spacer(1, 3*mm))

    # ── TOP PRIORITY FIXES ────────────────────────────────────────────────────
    if fixes:
        story.append(Spacer(1, 2*mm))
        story.extend(_section("🎯  TOP PRIORITY FIXES", st))

        story.append(_styled_table(
            [[Paragraph(f"#{i+1}",
                        S("fn",fontSize=12,textColor=ORANGE,
                          fontName="Helvetica-Bold",alignment=TA_CENTER)),
              Paragraph(f"<b>{f['check']}</b><br/>"
                        f"<font color='#A0AEC0'>{f['fix']}</font>",
                        S("ft",fontSize=8.5,textColor=WHITE,
                          fontName="Helvetica",leading=13)),
              Paragraph(f"<font color='#FF8C3A'><b>{f.get('service','')}</b></font>",
                        S("fs",fontSize=8,textColor=ORANGE_LT,
                          fontName="Helvetica",alignment=TA_RIGHT,leading=12))]
             for i,f in enumerate(fixes[:5])],
            [CW*0.06, CW*0.69, CW*0.25],
            [("ROWBACKGROUNDS",(0,0),(-1,-1),[NAVY_LIGHT,NAVY_MID]),
             ("TOPPADDING",(0,0),(-1,-1),9),
             ("BOTTOMPADDING",(0,0),(-1,-1),9),
             ("LEFTPADDING",(0,0),(-1,-1),9),
             ("RIGHTPADDING",(-1,0),(-1,-1),9),
             ("VALIGN",(0,0),(-1,-1),"TOP"),
             ("LINEABOVE",(0,0),(-1,0),1.5,ORANGE)],
        ))
        story.append(Spacer(1, 5*mm))

    # ── AI INSIGHT + CTA ──────────────────────────────────────────────────────
    cta_t = _styled_table(
        [[Paragraph(
            f"<b>{ai_insights.get('insight','')}</b><br/><br/>"
            f"<font color='#FF8C3A'>{ai_insights.get('cta','')}</font>",
            S("cta",fontSize=9.5,textColor=WHITE,fontName="Helvetica",leading=15)
        )]],
        [CW],
        [("BACKGROUND",(0,0),(-1,-1),NAVY_LIGHT),
         ("TOPPADDING",(0,0),(-1,-1),14),
         ("BOTTOMPADDING",(0,0),(-1,-1),14),
         ("LEFTPADDING",(0,0),(-1,-1),16),
         ("RIGHTPADDING",(-1,0),(-1,-1),16),
         ("LINEABOVE",(0,0),(-1,0),2,ORANGE),
         ("LINEBELOW",(0,0),(-1,-1),2,ORANGE)],
    )
    story.append(cta_t)
    story.append(Spacer(1, 5*mm))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(_styled_table(
        [[Paragraph("📞 +91 8589999362",st["small"]),
          Paragraph("✉️  Info@realsdigitalinnovations.com",st["small"]),
          Paragraph("🌐 realsdigitalinnovations.com",st["small"]),
          Paragraph("📍 Kannur, Kerala, India",st["small"])]],
        [CW/4]*4,
        [("BACKGROUND",(0,0),(-1,-1),NAVY_MID),
         ("TOPPADDING",(0,0),(-1,-1),7),
         ("BOTTOMPADDING",(0,0),(-1,-1),7),
         ("ALIGN",(0,0),(-1,-1),"CENTER"),
         ("VALIGN",(0,0),(-1,-1),"MIDDLE")],
    ))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg)
    return buf.getvalue()
