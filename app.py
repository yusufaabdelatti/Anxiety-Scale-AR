import streamlit as st
import requests
import smtplib
import os
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

GMAIL_ADDRESS   = "Wijdan.psyc@gmail.com"
GMAIL_PASSWORD  = "rias eeul lyuu stce"
THERAPIST_EMAIL = "Wijdan.psyc@gmail.com"
LOGO_FILE       = "logo.png"

# ══════════════════════════════════════════════════════════════
#  BAI — 21 فقرة، مقياس 0–3
# ══════════════════════════════════════════════════════════════

BAI_QUESTIONS = [
    {"id": 1,  "text": "خدر أو وخز (تنميل)"},
    {"id": 2,  "text": "الشعور بالحرارة"},
    {"id": 3,  "text": "ارتعاش في الساقين"},
    {"id": 4,  "text": "عدم القدرة على الاسترخاء"},
    {"id": 5,  "text": "الخوف من حدوث الأسوأ"},
    {"id": 6,  "text": "الدوار أو الإحساس بالإغماء"},
    {"id": 7,  "text": "خفقان أو تسارع ضربات القلب"},
    {"id": 8,  "text": "عدم الثبات أو الترنح"},
    {"id": 9,  "text": "الشعور بالرعب أو الخوف الشديد"},
    {"id": 10, "text": "العصبية والتوتر"},
    {"id": 11, "text": "الإحساس بالاختناق"},
    {"id": 12, "text": "ارتجاف اليدين"},
    {"id": 13, "text": "الارتعاش أو عدم الاستقرار"},
    {"id": 14, "text": "الخوف من فقدان السيطرة"},
    {"id": 15, "text": "صعوبة في التنفس"},
    {"id": 16, "text": "الخوف من الموت"},
    {"id": 17, "text": "الإحساس بالفزع"},
    {"id": 18, "text": "اضطراب في المعدة أو عسر الهضم"},
    {"id": 19, "text": "الإغماء أو الدوار"},
    {"id": 20, "text": "احمرار الوجه"},
    {"id": 21, "text": "التعرق الساخن أو البارد"},
]

BAI_SCALE = {
    0: "٠ — لا يوجد على الإطلاق",
    1: "١ — بدرجة خفيفة، ولم يزعجني كثيراً",
    2: "٢ — بدرجة متوسطة، كان مزعجاً أحياناً",
    3: "٣ — بدرجة شديدة، أزعجني كثيراً",
}

# ══════════════════════════════════════════════════════════════
#  PSWQ — 16 فقرة، مقياس 1–5
#  الفقرات المعكوسة: 1، 3، 8، 10، 11
# ══════════════════════════════════════════════════════════════

PSWQ_QUESTIONS = [
    {"id": 1,  "text": "إذا لم يكن لديّ وقت كافٍ لإنجاز كل شيء، فإنني لا أقلق حيال ذلك.",                       "reverse": True},
    {"id": 2,  "text": "قلقي يطغى عليّ ويسيطر على تفكيري.",                                                        "reverse": False},
    {"id": 3,  "text": "لا أميل إلى القلق على الأمور.",                                                             "reverse": True},
    {"id": 4,  "text": "مواقف كثيرة تجعلني أشعر بالقلق.",                                                          "reverse": False},
    {"id": 5,  "text": "أعلم أنه لا ينبغي لي القلق، لكنني لا أستطيع منع نفسي من ذلك.",                            "reverse": False},
    {"id": 6,  "text": "حين أكون تحت الضغط، أقلق كثيراً.",                                                         "reverse": False},
    {"id": 7,  "text": "أنا دائماً قلق بشأن شيء ما.",                                                               "reverse": False},
    {"id": 8,  "text": "أجد سهولة في التخلص من الأفكار المقلقة.",                                                   "reverse": True},
    {"id": 9,  "text": "بمجرد أن أنتهي من مهمة، أبدأ في القلق على كل ما تبقى عليّ إنجازه.",                       "reverse": False},
    {"id": 10, "text": "لا أقلق أبداً على أي شيء.",                                                                 "reverse": True},
    {"id": 11, "text": "حين لا يعود بإمكاني فعل أي شيء حيال مشكلة ما، أتوقف عن القلق بشأنها.",                   "reverse": True},
    {"id": 12, "text": "كنت شخصاً قلقاً طوال حياتي.",                                                               "reverse": False},
    {"id": 13, "text": "ألاحظ أنني أظل قلقاً على أمور كثيرة.",                                                      "reverse": False},
    {"id": 14, "text": "حين أبدأ بالقلق، لا أستطيع التوقف.",                                                        "reverse": False},
    {"id": 15, "text": "أقلق في كل وقت.",                                                                            "reverse": False},
    {"id": 16, "text": "أقلق على المشاريع حتى يتم إنجازها بالكامل.",                                                "reverse": False},
]

PSWQ_SCALE = {
    1: "١ — لا تنطبق عليّ على الإطلاق",
    2: "٢",
    3: "٣",
    4: "٤",
    5: "٥ — تنطبق عليّ تماماً",
}

# ══════════════════════════════════════════════════════════════
#  SCORING
# ══════════════════════════════════════════════════════════════

def calculate_bai_total(responses: dict) -> int:
    return sum(responses.values())

def get_bai_level(total: int) -> str:
    if total <= 21:   return "Low Anxiety"
    elif total <= 35: return "Moderate Anxiety"
    else:             return "Potentially Concerning Levels of Anxiety"

def get_bai_color(total: int) -> str:
    if total <= 21:   return "#5CB85C"
    elif total <= 35: return "#F0AD4E"
    else:             return "#D9534F"

def calculate_pswq_total(responses: dict) -> int:
    total = 0
    for q in PSWQ_QUESTIONS:
        raw = responses[q["id"]]
        scored = (6 - raw) if q["reverse"] else raw
        total += scored
    return total

def get_pswq_level(total: int) -> str:
    if total <= 44:   return "Low Worry"
    elif total <= 59: return "Moderate Worry"
    elif total <= 69: return "High Worry"
    else:             return "Very High Worry"

def get_pswq_color(total: int) -> str:
    if total <= 44:   return "#5CB85C"
    elif total <= 59: return "#F0AD4E"
    elif total <= 69: return "#E07B39"
    else:             return "#D9534F"

# ══════════════════════════════════════════════════════════════
#  GROQ REPORT — English, identical to English version
# ══════════════════════════════════════════════════════════════

def generate_report(client_name: str, bai_total: int, bai_responses: dict,
                    pswq_total: int, pswq_responses: dict) -> str:

    bai_level  = get_bai_level(bai_total)
    pswq_level = get_pswq_level(pswq_total)

    BAI_EN = [
        "Numbness or tingling", "Feeling hot", "Wobbliness in legs",
        "Unable to relax", "Fear of worst happening", "Dizzy or lightheaded",
        "Heart pounding / racing", "Unsteady", "Terrified or afraid",
        "Nervous", "Feeling of choking", "Hands trembling",
        "Shaky / unsteady", "Fear of losing control", "Difficulty in breathing",
        "Fear of dying", "Scared", "Indigestion",
        "Faint / lightheaded", "Face flushed", "Hot / cold sweats",
    ]
    PSWQ_EN = [
        "If I do not have enough time to do everything, I do not worry about it.",
        "My worries overwhelm me.",
        "I do not tend to worry about things.",
        "Many situations make me worry.",
        "I know I should not worry about things, but I just cannot help it.",
        "When I am under pressure I worry a lot.",
        "I am always worrying about something.",
        "I find it easy to dismiss worrisome thoughts.",
        "As soon as I finish one task, I start to worry about everything else I have to do.",
        "I never worry about anything.",
        "When there is nothing more I can do about a concern, I do not worry about it any more.",
        "I have been a worrier all my life.",
        "I notice that I have been worrying about things.",
        "Once I start worrying, I cannot stop.",
        "I worry all the time.",
        "I worry about projects until they are all done.",
    ]

    bai_items = "\n".join(
        f"  {BAI_EN[i]}: {bai_responses[q['id']]}/3"
        for i, q in enumerate(BAI_QUESTIONS)
    )

    pswq_items = "\n".join(
        f"  {'[R] ' if q['reverse'] else '      '}{PSWQ_EN[i]}: raw={pswq_responses[q['id']]}, scored={(6 - pswq_responses[q['id']]) if q['reverse'] else pswq_responses[q['id']]}"
        for i, q in enumerate(PSWQ_QUESTIONS)
    )

    prompt = f"""You are a licensed clinical psychologist writing a confidential dual-instrument anxiety assessment report.

CLIENT: {client_name}
DATE: {datetime.datetime.now().strftime("%B %d, %Y")}

════════════════════════════════
INSTRUMENT 1: Beck Anxiety Inventory (BAI)
21 items · scale 0–3 · range 0–63
Total: {bai_total}/63 — {bai_level}
Scoring: 0–21 Low · 22–35 Moderate · 36–63 Concerning
Reliability: α=0.92 · test-retest r=0.75
Reference: Beck et al. (1988), J. Consulting and Clinical Psychology, 56, 893–897.

Item responses:
{bai_items}

════════════════════════════════
INSTRUMENT 2: Penn State Worry Questionnaire (PSWQ)
16 items · scale 1–5 · range 16–80 · [R] = reverse scored
Total: {pswq_total}/80 — {pswq_level}
Scoring: ≤44 Low · 45–59 Moderate · 60–69 High · 70–80 Very High
Reliability: α=0.93 · test-retest r=0.92
Reference: Meyer et al. (1990), Behaviour Research and Therapy, 28, 487–495.

Item responses ([R] = reverse scored):
{pswq_items}

════════════════════════════════
REPORT INSTRUCTIONS:

Write a professional clinical report with these clearly labelled sections.

SECTION A — BECK ANXIETY INVENTORY (BAI)

A1. PRESENTING SYMPTOM PROFILE
Summarize the overall anxiety presentation from the BAI. Identify dominant symptom clusters (physiological, cognitive, affective) based on the item pattern.

A2. SYMPTOM ANALYSIS
Group items by cluster. Highlight the most severely endorsed items and their clinical significance. Note any interesting patterns or low-severity items suggesting resilience.

A3. SEVERITY & CLINICAL INTERPRETATION
Interpret the total score level. Note implications for daily functioning and any items warranting clinical attention.

────────────────────────────────
SECTION B — PENN STATE WORRY QUESTIONNAIRE (PSWQ)

B1. WORRY PROFILE
Summarize the worry presentation. Note the total score, level, and key endorsed items.

B2. WORRY PATTERN ANALYSIS
Identify the nature of worry (pervasive, uncontrollable, situation-specific). Highlight the highest-scoring items. Note any low-scored items indicating protective factors.

B3. SEVERITY & CLINICAL INTERPRETATION
Interpret the PSWQ score in the context of GAD screening thresholds (scores ≥45 suggest clinically significant worry).

────────────────────────────────
SECTION C — INTEGRATED ANXIETY PROFILE

C1. CROSS-INSTRUMENT SYNTHESIS
Synthesize findings from both instruments. Describe how the BAI somatic/physiological picture and the PSWQ cognitive worry pattern interact.

C2. CLINICAL FORMULATION
Outline a brief formulation: what type of anxiety presentation this pattern suggests and what maintains the anxiety.

C3. THERAPEUTIC IMPLICATIONS
Evidence-based treatment recommendations from the combined profile. 1 paragraph.

────────────────────────────────
SECTION D — SUMMARY

One concise paragraph:
"According to the Beck Anxiety Inventory (BAI), {client_name} self-reports [BAI score]/63, indicating [BAI level], with predominant [symptom clusters]. The Penn State Worry Questionnaire (PSWQ) yields a score of [PSWQ score]/80, indicating [PSWQ level], characterized by [worry pattern]. Taken together, these findings suggest [integrated interpretation]."

────────────────────────────────
FORMATTING RULES:
- Use the section labels exactly as above (A1, A2, etc.)
- No preamble or closing remarks outside the sections
- No repetition of the same point across sections
- Clinical, precise language throughout"""

    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from Streamlit secrets.")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.4,
        },
        timeout=90,
    )

    if not response.ok:
        try:    error_detail = response.json()
        except: error_detail = response.text
        raise Exception(f"Groq API error {response.status_code}: {error_detail}")

    return response.json()["choices"][0]["message"]["content"].strip()

# ══════════════════════════════════════════════════════════════
#  PDF — identical to English version
# ══════════════════════════════════════════════════════════════

def create_pdf_report(path, client_name, bai_total, bai_responses,
                      pswq_total, pswq_responses, report_text, timestamp):

    DARK   = colors.HexColor("#1C1917")
    WARM   = colors.HexColor("#6B5B45")
    LIGHT  = colors.HexColor("#F7F4F0")
    BORDER = colors.HexColor("#DDD5C8")

    bai_lvl_color  = colors.HexColor(get_bai_color(bai_total))
    pswq_lvl_color = colors.HexColor(get_pswq_color(pswq_total))

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    title_s   = ParagraphStyle("T",  fontName="Times-Roman",      fontSize=20, textColor=DARK,  alignment=TA_CENTER, spaceAfter=3)
    sub_s     = ParagraphStyle("S",  fontName="Times-Italic",      fontSize=10, textColor=WARM,  alignment=TA_CENTER, spaceAfter=2)
    meta_s    = ParagraphStyle("M",  fontName="Helvetica",         fontSize=8,  textColor=WARM,  alignment=TA_CENTER, spaceAfter=12)
    section_s = ParagraphStyle("Se", fontName="Helvetica-Bold",    fontSize=10, textColor=WARM,  spaceBefore=12, spaceAfter=4)
    body_s    = ParagraphStyle("B",  fontName="Helvetica",         fontSize=9.5,textColor=DARK,  leading=15, spaceAfter=5)
    small_s   = ParagraphStyle("Sm", fontName="Helvetica",         fontSize=8.5,textColor=WARM,  leading=13)
    footer_s  = ParagraphStyle("Ft", fontName="Helvetica-Oblique", fontSize=7.5,textColor=WARM,  leading=11, alignment=TA_CENTER)

    story = []
    date_str = datetime.datetime.now().strftime("%B %d, %Y  |  %H:%M")

    if os.path.exists(LOGO_FILE):
        try:
            logo = RLImage(LOGO_FILE, width=4*cm, height=2*cm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 0.3*cm))
        except Exception:
            pass

    story.append(Paragraph("Anxiety Assessment Report", title_s))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Beck Anxiety Inventory  ·  Penn State Worry Questionnaire", sub_s))
    story.append(Paragraph(f"CONFIDENTIAL  ·  {date_str}", meta_s))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.3*cm))

    info_data = [
        [Paragraph("<b>Client</b>", small_s), Paragraph(client_name, body_s),
         Paragraph("<b>Assessments</b>", small_s), Paragraph("BAI (21 items) · PSWQ (16 items)", body_s)],
        [Paragraph("<b>Date</b>", small_s), Paragraph(date_str, body_s),
         Paragraph("<b>Score Ranges</b>", small_s), Paragraph("BAI: 0–63  |  PSWQ: 16–80", body_s)],
    ]
    it = Table(info_data, colWidths=[3*cm, 6*cm, 3.5*cm, 4.5*cm])
    it.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), LIGHT),
        ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ]))
    story.append(it)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("SCORE SUMMARY", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    def bar(score, max_score, width=30):
        filled = max(0, min(width, int((score / max_score) * width)))
        return "█" * filled + "░" * (width - filled)

    summary_header = [
        Paragraph("<b>Instrument</b>", small_s),
        Paragraph("<b>Score</b>",      small_s),
        Paragraph("<b>Level</b>",      small_s),
        Paragraph("<b>Range Bar</b>",  small_s),
    ]
    summary_rows = [summary_header, [
        Paragraph("<b>Beck Anxiety Inventory (BAI)</b>",
                  ParagraphStyle("bi", fontName="Helvetica-Bold", fontSize=9, textColor=bai_lvl_color)),
        Paragraph(f"<b>{bai_total}/63</b>",
                  ParagraphStyle("bs", fontName="Helvetica-Bold", fontSize=9, textColor=bai_lvl_color, alignment=TA_CENTER)),
        Paragraph(get_bai_level(bai_total),
                  ParagraphStyle("bl", fontName="Helvetica", fontSize=8.5, textColor=bai_lvl_color)),
        Paragraph(f'<font color="{get_bai_color(bai_total)}">{bar(bai_total, 63)}</font>',
                  ParagraphStyle("bb", fontName="Courier", fontSize=7)),
    ], [
        Paragraph("<b>Penn State Worry Questionnaire (PSWQ)</b>",
                  ParagraphStyle("pi", fontName="Helvetica-Bold", fontSize=9, textColor=pswq_lvl_color)),
        Paragraph(f"<b>{pswq_total}/80</b>",
                  ParagraphStyle("ps", fontName="Helvetica-Bold", fontSize=9, textColor=pswq_lvl_color, alignment=TA_CENTER)),
        Paragraph(get_pswq_level(pswq_total),
                  ParagraphStyle("pl", fontName="Helvetica", fontSize=8.5, textColor=pswq_lvl_color)),
        Paragraph(f'<font color="{get_pswq_color(pswq_total)}">{bar(pswq_total, 80)}</font>',
                  ParagraphStyle("pb", fontName="Courier", fontSize=7)),
    ]]

    sum_table = Table(summary_rows, colWidths=[5.5*cm, 2*cm, 4.5*cm, 5*cm])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#EDE9E3")),
        ("BACKGROUND",    (0,2),(-1,2),  LIGHT),
        ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN",         (1,0),(1,-1),  "CENTER"),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.4*cm))

    # ── BAI item table ────────────────────────────────────────
    story.append(Paragraph("BECK ANXIETY INVENTORY — ITEM RESPONSES", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    SCORE_LABELS = {0: "Not at all", 1: "Mildly", 2: "Moderately", 3: "Severely"}
    SCORE_COLORS = {
        0: colors.HexColor("#5CB85C"), 1: colors.HexColor("#F0AD4E"),
        2: colors.HexColor("#E07B39"), 3: colors.HexColor("#D9534F"),
    }

    bai_header = [
        Paragraph("<b>#</b>",        small_s),
        Paragraph("<b>Symptom</b>",  small_s),
        Paragraph("<b>Score</b>",    small_s),
        Paragraph("<b>Severity</b>", small_s),
    ]
    bai_rows = [bai_header]

    # Map Arabic symptom text back to English for the PDF
    BAI_EN = [
        "Numbness or tingling", "Feeling hot", "Wobbliness in legs",
        "Unable to relax", "Fear of worst happening", "Dizzy or lightheaded",
        "Heart pounding / racing", "Unsteady", "Terrified or afraid",
        "Nervous", "Feeling of choking", "Hands trembling",
        "Shaky / unsteady", "Fear of losing control", "Difficulty in breathing",
        "Fear of dying", "Scared", "Indigestion",
        "Faint / lightheaded", "Face flushed", "Hot / cold sweats",
    ]

    for idx, q in enumerate(BAI_QUESTIONS):
        sc = bai_responses[q["id"]]
        sc_col = SCORE_COLORS[sc]
        bai_rows.append([
            Paragraph(str(q["id"]),
                      ParagraphStyle("in", fontName="Helvetica", fontSize=8.5, textColor=WARM, alignment=TA_CENTER)),
            Paragraph(BAI_EN[idx], body_s),
            Paragraph(f"<b>{sc}</b>",
                      ParagraphStyle("is", fontName="Helvetica-Bold", fontSize=9, textColor=sc_col, alignment=TA_CENTER)),
            Paragraph(SCORE_LABELS[sc],
                      ParagraphStyle("il", fontName="Helvetica", fontSize=8.5, textColor=sc_col)),
        ])

    bai_table = Table(bai_rows, colWidths=[1.2*cm, 8.5*cm, 1.8*cm, 5.5*cm])
    bai_styles = [
        ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#EDE9E3")),
        ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("ALIGN",         (0,0),(0,-1),  "CENTER"),
        ("ALIGN",         (2,0),(2,-1),  "CENTER"),
    ]
    for i in range(1, len(bai_rows)):
        if i % 2 == 0:
            bai_styles.append(("BACKGROUND", (0,i),(-1,i), LIGHT))
    bai_table.setStyle(TableStyle(bai_styles))
    story.append(bai_table)
    story.append(Spacer(1, 0.5*cm))

    # ── PSWQ item table ───────────────────────────────────────
    story.append(Paragraph("PENN STATE WORRY QUESTIONNAIRE — ITEM RESPONSES", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    PSWQ_EN = [
        "If I do not have enough time to do everything, I do not worry about it.",
        "My worries overwhelm me.",
        "I do not tend to worry about things.",
        "Many situations make me worry.",
        "I know I should not worry about things, but I just cannot help it.",
        "When I am under pressure I worry a lot.",
        "I am always worrying about something.",
        "I find it easy to dismiss worrisome thoughts.",
        "As soon as I finish one task, I start to worry about everything else I have to do.",
        "I never worry about anything.",
        "When there is nothing more I can do about a concern, I do not worry about it any more.",
        "I have been a worrier all my life.",
        "I notice that I have been worrying about things.",
        "Once I start worrying, I cannot stop.",
        "I worry all the time.",
        "I worry about projects until they are all done.",
    ]

    pswq_header = [
        Paragraph("<b>#</b>",         small_s),
        Paragraph("<b>Statement</b>", small_s),
        Paragraph("<b>Raw</b>",       small_s),
        Paragraph("<b>Scored</b>",    small_s),
    ]
    pswq_rows = [pswq_header]

    def pswq_score_color(scored):
        if scored <= 2:   return colors.HexColor("#5CB85C")
        elif scored == 3: return colors.HexColor("#F0AD4E")
        elif scored == 4: return colors.HexColor("#E07B39")
        else:             return colors.HexColor("#D9534F")

    for idx, q in enumerate(PSWQ_QUESTIONS):
        raw    = pswq_responses[q["id"]]
        scored = (6 - raw) if q["reverse"] else raw
        sc_col = pswq_score_color(scored)
        rev_tag = " <i>[R]</i>" if q["reverse"] else ""
        pswq_rows.append([
            Paragraph(str(q["id"]),
                      ParagraphStyle("pn", fontName="Helvetica", fontSize=8.5, textColor=WARM, alignment=TA_CENTER)),
            Paragraph(PSWQ_EN[idx] + rev_tag,
                      ParagraphStyle("pt", fontName="Helvetica", fontSize=9, textColor=DARK, leading=13)),
            Paragraph(str(raw),
                      ParagraphStyle("pr", fontName="Helvetica", fontSize=9, textColor=WARM, alignment=TA_CENTER)),
            Paragraph(f"<b>{scored}</b>",
                      ParagraphStyle("ps2", fontName="Helvetica-Bold", fontSize=9, textColor=sc_col, alignment=TA_CENTER)),
        ])

    pswq_table = Table(pswq_rows, colWidths=[1.2*cm, 10*cm, 1.5*cm, 2.3*cm])
    pswq_styles = [
        ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#EDE9E3")),
        ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("ALIGN",         (0,0),(0,-1),  "CENTER"),
        ("ALIGN",         (2,0),(3,-1),  "CENTER"),
    ]
    for i in range(1, len(pswq_rows)):
        if i % 2 == 0:
            pswq_styles.append(("BACKGROUND", (0,i),(-1,i), LIGHT))
    pswq_table.setStyle(TableStyle(pswq_styles))
    story.append(pswq_table)

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "<i>[R] = reverse scored item. Scored value reflects the transformed score used in the total.</i>",
        ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=7.5, textColor=WARM)
    ))
    story.append(Spacer(1, 0.5*cm))

    # ── Clinical report ───────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("CLINICAL REPORT", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    for line in report_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.18*cm))
        elif line.isupper() or (line.endswith(":") and len(line) < 70) or (
            line[:3] in ("A1.", "A2.", "A3.", "B1.", "B2.", "B3.", "C1.", "C2.", "C3.", "D. ", "D —")
            or line.startswith("SECTION")
        ):
            story.append(Paragraph(line, section_s))
        else:
            story.append(Paragraph(line, body_s))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This report is strictly confidential and intended solely for the treating clinician. "
        "Not to be shared without explicit written consent. "
        "AI-assisted analysis should be reviewed alongside clinical judgment.",
        footer_s
    ))
    doc.build(story)

# ══════════════════════════════════════════════════════════════
#  EMAIL
# ══════════════════════════════════════════════════════════════

def send_report_email(pdf_path, client_name, bai_total, pswq_total, filename):
    date_str   = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")
    bai_color  = get_bai_color(bai_total)
    pswq_color = get_pswq_color(pswq_total)

    msg = MIMEMultipart("mixed")
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = THERAPIST_EMAIL
    msg["Subject"] = f"[Anxiety Report] {client_name} — {date_str}"

    body_html = f"""
    <html><body style="font-family:Georgia,serif;color:#1C1917;background:#F7F4F0;padding:24px;">
      <div style="max-width:580px;margin:0 auto;background:white;border:1px solid #DDD5C8;border-radius:4px;padding:32px;">
        <h2 style="font-weight:300;font-size:22px;margin-bottom:2px;">Anxiety Assessment Report</h2>
        <p style="color:#6B5B45;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;margin-top:0;">
          BAI · PSWQ — New Submission
        </p>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <table style="width:100%;font-size:14px;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#6B5B45;width:40%;">Client</td><td><strong>{client_name}</strong></td></tr>
          <tr><td style="padding:6px 0;color:#6B5B45;">Date &amp; Time</td><td>{date_str}</td></tr>
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <p style="font-size:13px;color:#6B5B45;margin-bottom:8px;font-weight:bold;">Assessment Results</p>
        <table style="width:100%;font-size:13px;border-collapse:collapse;">
          <tr>
            <td style="padding:6px 0;color:#6B5B45;width:50%;">BAI Total Score</td>
            <td><strong style="color:{bai_color};">{bai_total}/63 — {get_bai_level(bai_total)}</strong></td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B5B45;">PSWQ Total Score</td>
            <td><strong style="color:{pswq_color};">{pswq_total}/80 — {get_pswq_level(pswq_total)}</strong></td>
          </tr>
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <p style="font-size:13px;line-height:1.6;">The full clinical report is attached as a PDF.</p>
        <p style="font-size:11px;color:#6B5B45;margin-top:20px;font-style:italic;">
          Confidential — intended only for the treating clinician.</p>
      </div>
    </body></html>"""

    msg.attach(MIMEText(body_html, "html"))
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, THERAPIST_EMAIL, msg.as_string())

# ══════════════════════════════════════════════════════════════
#  STREAMLIT UI — Arabic interface
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="تقييم القلق",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg: #F7F4F0;
    --white: #FFFFFF;
    --deep: #1C1917;
    --warm: #6B5B45;
    --accent: #8B6F47;
    --border: #DDD5C8;
    --selected: #2D2926;
}

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden !important; display: none !important; }
header[data-testid="stHeader"] { visibility: hidden !important; display: none !important; }
footer { visibility: hidden !important; display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stActionButton"] { display: none !important; }
a[href*="streamlit.io"] { display: none !important; }
a[href*="share.streamlit.io"] { display: none !important; }
.viewerBadge_container__r5tak { display: none !important; }
.viewerBadge_link__qRIco { display: none !important; }
.styles_viewerBadge__CvC9N { display: none !important; }
[class*="viewerBadge"] { display: none !important; }
[class*="ProfileBadge"] { display: none !important; }
#stDecoration { display: none !important; }

/* ── Force light mode ── */
html, body, [data-theme="dark"], [data-theme="light"] { color-scheme: light only !important; }
[data-testid="stAppViewContainer"], .stApp {
    background-color: #F7F4F0 !important;
    color: #1C1917 !important;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--deep);
    direction: rtl;
}
.stApp { background-color: var(--bg); }

.page-header {
    text-align: center;
    padding: 2.5rem 0 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
    direction: rtl;
}
.page-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 400;
    margin-bottom: 0.3rem;
    color: var(--deep);
}
.page-header p {
    color: var(--warm);
    font-size: 0.82rem;
    letter-spacing: 0.06em;
    font-weight: 400;
}

.section-divider {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid var(--border);
    margin: 2rem 0 1.5rem 0;
    direction: rtl;
}
.section-divider h2 {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 400;
    color: var(--deep);
    margin-bottom: 0.2rem;
}
.section-divider p {
    color: var(--warm);
    font-size: 0.78rem;
    letter-spacing: 0.06em;
}

.question-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.5rem 1.8rem 0.5rem 1.8rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
    direction: rtl;
    text-align: right;
}
.question-card:hover { border-color: var(--accent); }

.q-number {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: var(--accent);
    margin-bottom: 0.3rem;
    font-weight: 500;
}
.q-text {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    color: var(--deep);
    margin-bottom: 1rem;
    line-height: 1.6;
}

div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] > div {
    gap: 0.4rem !important;
    flex-direction: row-reverse !important;
    flex-wrap: wrap !important;
    justify-content: flex-start !important;
}
div[data-testid="stRadio"] > div > label {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 0.45rem 0.9rem !important;
    cursor: pointer !important;
    font-size: 0.82rem !important;
    color: var(--deep) !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
}
div[data-testid="stRadio"] > div > label:hover {
    border-color: var(--accent) !important;
    background: #F0EBE3 !important;
}

.progress-wrap { background: var(--border); border-radius: 2px; height: 3px; margin: 1.5rem 0 0.5rem 0; }
.progress-fill { height: 3px; border-radius: 2px; background: linear-gradient(90deg, var(--warm), var(--accent)); }

.stButton > button {
    background: var(--selected) !important;
    color: var(--bg) !important;
    border: none !important;
    padding: 0.8rem 2.8rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    border-radius: 2px !important;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background: var(--warm) !important; }

.thank-you {
    text-align: center;
    padding: 5rem 2rem;
    direction: rtl;
}
.thank-you h2 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 400;
    margin-bottom: 1rem;
}
.thank-you p {
    color: var(--warm);
    font-size: 0.95rem;
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.9;
}

div[data-testid="stTextInput"] input {
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--deep) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Routing ────────────────────────────────────────────────────────────────────
page = st.query_params.get("page", "client")

if page == "admin":
    st.markdown("""
    <div class="page-header">
        <p>بوابة المعالج</p>
        <h1>التقارير المحفوظة</h1>
    </div>""", unsafe_allow_html=True)

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        if st.button("دخول"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة.")
    else:
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        files = sorted([f for f in os.listdir(reports_dir) if f.endswith(".pdf")], reverse=True)
        if not files:
            st.info("لا توجد تقارير مسجّلة حتى الآن.")
        else:
            st.markdown(f"**{len(files)} تقرير محفوظ**")
            for fname in files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📄 `{fname}`")
                with col2:
                    with open(os.path.join(reports_dir, fname), "rb") as f:
                        st.download_button("تحميل", data=f, file_name=fname,
                                           mime="application/pdf", key=fname)
        if st.button("تسجيل الخروج"):
            st.session_state.admin_auth = False
            st.rerun()

else:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if st.session_state.submitted:
        st.markdown("""
        <div class="thank-you">
            <h2>شكراً لك</h2>
            <p>تم تسليم إجاباتك بنجاح.<br>
            سيتواصل معك المعالج في أقرب وقت.</p>
        </div>""", unsafe_allow_html=True)
        if st.session_state.get("email_error"):
            st.warning(f"ملاحظة: فشل إرسال البريد — {st.session_state.email_error}")

    else:
        if os.path.exists(LOGO_FILE):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(LOGO_FILE, use_container_width=True)

        st.markdown("""
        <div class="page-header">
            <p>تقييم نفسي سري</p>
            <h1>استبيانات القلق</h1>
        </div>""", unsafe_allow_html=True)

        client_name = st.text_input(
            "اسمك باللغة الإنجليزية (اختياري)",
            placeholder="Your name in English"
        )

        # ── PART 1: BAI ───────────────────────────────────────────────────────
        st.markdown("""
        <div class="section-divider">
            <h2>الجزء الأول — مقياس بيك للقلق</h2>
            <p>٢١ فقرة · الشهر الماضي · مقياس ٠–٣</p>
        </div>
        <p style="font-size:0.88rem;color:#6B5B45;text-align:center;margin-bottom:1.5rem;
                  line-height:1.9;direction:rtl;">
        حدّد مدى <strong>إزعاج كل عَرَض لك خلال الشهر الماضي</strong>، بما في ذلك اليوم.
        </p>""", unsafe_allow_html=True)

        bai_responses    = {}
        bai_all_answered = True

        for q in BAI_QUESTIONS:
            qid = q["id"]
            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">العَرَض {qid} من ٢١</div>
                <div class="q-text">{q['text']}</div>
            </div>""", unsafe_allow_html=True)

            choice = st.radio(
                label=f"bai_{qid}",
                options=list(BAI_SCALE.values()),
                index=None,
                key=f"bai_{qid}",
                label_visibility="collapsed",
                horizontal=True,
            )
            if choice is None:
                bai_all_answered = False
            else:
                bai_responses[qid] = next(k for k, v in BAI_SCALE.items() if v == choice)

        # ── PART 2: PSWQ ─────────────────────────────────────────────────────
        st.markdown("""
        <div class="section-divider">
            <h2>الجزء الثاني — استبيان القلق لجامعة بن ستيت</h2>
            <p>١٦ فقرة · بشكل عام · مقياس ١–٥</p>
        </div>
        <p style="font-size:0.88rem;color:#6B5B45;text-align:center;margin-bottom:1.5rem;
                  line-height:1.9;direction:rtl;">
        قيّم كل عبارة بحسب <strong>مدى انطباقها عليك بشكل عام</strong>.<br>
        ابدأ كل عبارة بـ <strong>"أنا..."</strong> وأجب بناءً على طبيعتك المعتادة.
        </p>""", unsafe_allow_html=True)

        pswq_responses    = {}
        pswq_all_answered = True

        for q in PSWQ_QUESTIONS:
            qid = q["id"]
            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">العبارة {qid} من ١٦</div>
                <div class="q-text">{q['text']}</div>
            </div>""", unsafe_allow_html=True)

            choice = st.radio(
                label=f"pswq_{qid}",
                options=list(PSWQ_SCALE.values()),
                index=None,
                key=f"pswq_{qid}",
                label_visibility="collapsed",
                horizontal=True,
            )
            if choice is None:
                pswq_all_answered = False
            else:
                pswq_responses[qid] = next(k for k, v in PSWQ_SCALE.items() if v == choice)

        # ── Progress ──────────────────────────────────────────────────────────
        total_q      = 21 + 16
        answered     = len(bai_responses) + len(pswq_responses)
        pct          = int((answered / total_q) * 100)
        all_answered = bai_all_answered and pswq_all_answered

        st.markdown(f"""
        <div style="text-align:center;font-size:0.78rem;color:#6B5B45;
                    letter-spacing:0.05em;margin-top:1.5rem;direction:rtl;">
            {answered} من {total_q} سؤالاً تمت الإجابة عنه
        </div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%"></div>
        </div>""", unsafe_allow_html=True)

        if not all_answered and answered > 0:
            st.markdown("""
            <div style="background:#FFF8F0;border-right:3px solid #E07B39;border-left:none;
                        padding:1rem 1.2rem;border-radius:4px 0 0 4px;
                        font-size:0.88rem;color:#7A3D1A;margin:1rem 0;
                        direction:rtl;text-align:right;">
                ⚠ يرجى الإجابة على جميع الأسئلة السبعة والثلاثين قبل التسليم.
            </div>""", unsafe_allow_html=True)

        # ── Name validation ───────────────────────────────────────────────────
        has_arabic_name = any('\u0600' <= c <= '\u06ff' for c in (client_name or ""))

        st.markdown('<div style="text-align:center;padding:2rem 0 3rem 0;">', unsafe_allow_html=True)
        submit = st.button("تسليم الاستبيان", disabled=not all_answered)
        st.markdown('</div>', unsafe_allow_html=True)

        if submit and has_arabic_name:
            st.markdown("""
            <div style="background:#FFF0F0;border-right:3px solid #D9534F;border-left:none;
                        padding:1rem 1.2rem;border-radius:4px 0 0 4px;
                        font-size:0.92rem;color:#7A1A1A;margin:0.5rem 0;
                        direction:rtl;text-align:right;font-weight:500;">
                ⚠ يرجى كتابة اسمك باللغة الإنجليزية فقط. الأسماء المكتوبة بالعربية غير مقبولة.
            </div>""", unsafe_allow_html=True)

        if submit and all_answered and not has_arabic_name:
            with st.spinner("جاري تسليم إجاباتك..."):
                bai_total  = calculate_bai_total(bai_responses)
                pswq_total = calculate_pswq_total(pswq_responses)
                report_text = generate_report(
                    client_name or "Anonymous",
                    bai_total, bai_responses,
                    pswq_total, pswq_responses,
                )

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = (client_name or "anonymous").replace(" ", "_").lower()
                filename  = f"Anxiety_{safe_name}_{timestamp}.pdf"
                os.makedirs("reports", exist_ok=True)
                pdf_path  = os.path.join("reports", filename)

                try:
                    create_pdf_report(
                        pdf_path, client_name or "Anonymous",
                        bai_total, bai_responses,
                        pswq_total, pswq_responses,
                        report_text, timestamp,
                    )
                except Exception as pdf_err:
                    st.error(f"خطأ في إنشاء التقرير: {pdf_err}")
                    st.stop()

                email_error = None
                try:
                    send_report_email(pdf_path, client_name or "Anonymous",
                                      bai_total, pswq_total, filename)
                except Exception as e:
                    email_error = str(e)

                st.session_state.submitted    = True
                st.session_state.email_error  = email_error
                st.rerun()
