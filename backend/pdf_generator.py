"""
pdf_generator.py — ReportLab PDF Creator for Legal Documents

Accepts the same structured document dict produced by document_generator.py
and returns a bytes object containing a well-formatted, multi-page PDF.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    ListFlowable, ListItem, Table, TableStyle, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------------------------------------------------------------------
# Colour palette (legal / professional)
# ---------------------------------------------------------------------------
DARK_NAVY   = colors.HexColor("#1a2744")
ACCENT_BLUE = colors.HexColor("#2563eb")
MID_GREY    = colors.HexColor("#6b7280")
LIGHT_GREY  = colors.HexColor("#f3f4f6")
WHITE       = colors.white
BLACK       = colors.black


def generate_pdf(doc_fields: dict) -> bytes:
    """
    Generate a properly formatted multi-page PDF from document fields.

    Args:
        doc_fields: The dict produced by document_generator.generate()
                    (or edited by the user in the frontend).

    Returns:
        PDF content as bytes.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=doc_fields.get("template_title", "Legal Notice"),
        author=doc_fields.get("sender_name", ""),
    )

    styles = _build_styles()
    story  = _build_story(doc_fields, styles)

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)

    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles():
    base = getSampleStyleSheet()
    s = {}

    s["doc_title"] = ParagraphStyle(
        "doc_title",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK_NAVY,
        alignment=TA_CENTER,
        spaceAfter=4,
        spaceBefore=6,
    )
    s["template_subtitle"] = ParagraphStyle(
        "template_subtitle",
        fontName="Helvetica",
        fontSize=10,
        textColor=ACCENT_BLUE,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    s["section_label"] = ParagraphStyle(
        "section_label",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=ACCENT_BLUE,
        spaceBefore=14,
        spaceAfter=4,
        letterSpacing=1,
    )
    s["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    s["body_bold"] = ParagraphStyle(
        "body_bold",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=4,
    )
    s["meta_label"] = ParagraphStyle(
        "meta_label",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=MID_GREY,
        spaceAfter=1,
    )
    s["meta_value"] = ParagraphStyle(
        "meta_value",
        fontName="Helvetica",
        fontSize=10,
        textColor=BLACK,
        spaceAfter=6,
    )
    s["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
        leftIndent=12,
        spaceAfter=3,
    )
    s["closing"] = ParagraphStyle(
        "closing",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        alignment=TA_JUSTIFY,
        spaceBefore=10,
        spaceAfter=6,
    )
    s["signature_label"] = ParagraphStyle(
        "signature_label",
        fontName="Helvetica",
        fontSize=9,
        textColor=MID_GREY,
        spaceAfter=2,
    )
    s["signature_name"] = ParagraphStyle(
        "signature_name",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=DARK_NAVY,
        spaceAfter=2,
    )

    return s


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------

def _build_story(fields: dict, styles: dict) -> list:
    f = fields
    story = []

    # ---- Document Title ----
    story.append(Paragraph(f.get("template_title", "Legal Notice"), styles["doc_title"]))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceAfter=8))

    # ---- Date + From/To metadata table ----
    date_str = f.get("date", datetime.today().strftime("%d %B %Y"))

    meta_data = [
        [
            _meta_block("DATE", date_str, styles),
            _meta_block("FROM", f"{f.get('sender_name','')}\n{f.get('sender_address','')}", styles),
            _meta_block("TO", f"{f.get('recipient_name','')}\n{f.get('recipient_address','')}", styles),
        ]
    ]
    meta_table = Table(meta_data, colWidths=["20%", "40%", "40%"])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEAFTER", (0, 0), (1, 0), 0.5, colors.HexColor("#d1d5db")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ---- Subject ----
    subject = f.get("subject", "Legal Notice")
    story.append(KeepTogether([
        Paragraph("SUBJECT", styles["section_label"]),
        Paragraph(f"<b>{subject}</b>", styles["body"]),
    ]))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"), spaceAfter=8))

    # ---- Opening paragraph ----
    story.append(Paragraph("Sir/Madam,", styles["body_bold"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f.get("opening", ""), styles["body"]))

    # ---- Facts ----
    facts = f.get("facts", [])
    if facts:
        story.append(KeepTogether([
            Paragraph("STATEMENT OF FACTS", styles["section_label"]),
            *[Paragraph(f"• {fact}", styles["bullet"]) for fact in facts],
        ]))

    # ---- Issue description ----
    issue_desc = f.get("issue_description", "")
    if issue_desc:
        story.append(Paragraph("NATURE OF GRIEVANCE", styles["section_label"]))
        story.append(Paragraph(issue_desc, styles["body"]))

    # ---- Amount ----
    amount = f.get("amount", "")
    if amount:
        story.append(KeepTogether([
            Paragraph("AMOUNT IN DISPUTE", styles["section_label"]),
            Paragraph(f"<b>{amount}</b>", styles["body"]),
        ]))

    # ---- Rights ----
    rights = f.get("rights", [])
    if rights:
        story.append(KeepTogether([
            Paragraph("LEGAL RIGHTS", styles["section_label"]),
            *[Paragraph(f"• {r}", styles["bullet"]) for r in rights],
        ]))

    # ---- Laws / Legal basis ----
    laws = f.get("laws", [])
    if laws:
        story.append(Paragraph("LEGAL BASIS", styles["section_label"]))
        for law in laws:
            act  = law.get("act", "")
            sec  = law.get("section", "")
            titl = law.get("title", "")
            expl = law.get("explanation", "")
            law_text = f"<b>{act} — {sec}: {titl}</b><br/>{expl}"
            story.append(Paragraph(law_text, styles["bullet"]))
            story.append(Spacer(1, 4))

    # ---- Relief requested ----
    relief = f.get("relief_requested", [])
    if relief:
        story.append(KeepTogether([
            Paragraph("RELIEF REQUESTED", styles["section_label"]),
            *[Paragraph(f"• {r}", styles["bullet"]) for r in relief],
        ]))

    # ---- Closing ----
    story.append(Paragraph(f.get("closing", ""), styles["closing"]))

    # ---- Signature block ----
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="40%", thickness=0.5, color=MID_GREY, spaceAfter=6))
    story.append(Paragraph("Yours faithfully,", styles["signature_label"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph(f.get("sender_name", ""), styles["signature_name"]))
    story.append(Paragraph(f.get("sender_address", ""), styles["signature_label"]))
    story.append(Paragraph(f"Date: {f.get('date', '')}", styles["signature_label"]))

    return story


def _meta_block(label: str, value: str, styles: dict):
    """Return a Paragraph-based cell for the metadata table."""
    lines = value.split("\n")
    content = f"<font size='8' color='#6b7280'><b>{label}</b></font><br/>"
    content += "<br/>".join(lines)
    return Paragraph(content, ParagraphStyle(
        f"meta_{label}",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=BLACK,
    ))


# ---------------------------------------------------------------------------
# Header / Footer callbacks
# ---------------------------------------------------------------------------

def _header_footer(canvas, doc):
    canvas.saveState()

    w, h = A4

    # Top accent bar
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, fill=True, stroke=False)

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2.5 * cm, h - 5.5 * mm, "LegalAId — Legal Document")

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 2.5 * cm, h - 5.5 * mm, "CONFIDENTIAL")

    # Bottom footer
    canvas.setFillColor(LIGHT_GREY)
    canvas.rect(0, 0, w, 1.4 * cm, fill=True, stroke=False)

    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2.5 * cm, 0.5 * cm, "Generated by LegalAId — For informational purposes only. Not legal advice.")
    canvas.drawRightString(w - 2.5 * cm, 0.5 * cm, f"Page {doc.page}")

    canvas.restoreState()
