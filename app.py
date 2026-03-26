import streamlit as st
import smtplib
import requests
import datetime
import os
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
from reportlab.lib.enums import TA_CENTER

GMAIL_ADDRESS   = "Wijdan.psyc@gmail.com"
GMAIL_PASSWORD  = "rias eeul lyuu stce"
THERAPIST_EMAIL = "Wijdan.psyc@gmail.com"
LOGO_FILE       = "logo.png"

BDI_QUESTIONS = [
    {"theme_ar": "الحزن", "theme_en": "Sadness", "options": [
        {"score": 0, "ar": "لا أشعر بالحزن.", "en": "I do not feel sad."},
        {"score": 1, "ar": "أشعر بالحزن.", "en": "I feel sad."},
        {"score": 2, "ar": "أشعر بالحزن طوال الوقت ولا أستطيع التخلص منه.", "en": "I am sad all the time and I can't snap out of it."},
        {"score": 3, "ar": "أشعر بحزن وتعاسة شديدَين لا أحتملهما.", "en": "I am so sad and unhappy that I can't stand it."},
    ]},
    {"theme_ar": "التشاؤم", "theme_en": "Pessimism", "options": [
        {"score": 0, "ar": "لست محبطاً من المستقبل بصفة خاصة.", "en": "I am not particularly discouraged about the future."},
        {"score": 1, "ar": "أشعر بالإحباط من المستقبل.", "en": "I feel discouraged about the future."},
        {"score": 2, "ar": "أشعر أنه لا يوجد شيء أتطلع إليه.", "en": "I feel I have nothing to look forward to."},
        {"score": 3, "ar": "أشعر أن المستقبل ميؤوس منه وأن الأمور لا يمكن أن تتحسن.", "en": "I feel the future is hopeless and that things cannot improve."},
    ]},
    {"theme_ar": "الشعور بالفشل", "theme_en": "Sense of Failure", "options": [
        {"score": 0, "ar": "لا أشعر أنني فاشل.", "en": "I do not feel like a failure."},
        {"score": 1, "ar": "أشعر أنني فشلت أكثر من الشخص العادي.", "en": "I feel I have failed more than the average person."},
        {"score": 2, "ar": "حين أنظر إلى حياتي الماضية لا أرى فيها إلا الفشل.", "en": "As I look back on my life, all I can see is a lot of failures."},
        {"score": 3, "ar": "أشعر أنني إنسان فاشل تماماً.", "en": "I feel I am a complete failure as a person."},
    ]},
    {"theme_ar": "فقدان الرضا", "theme_en": "Loss of Satisfaction", "options": [
        {"score": 0, "ar": "أشعر بالرضا عن الأشياء كما كنت من قبل.", "en": "I get as much satisfaction out of things as I used to."},
        {"score": 1, "ar": "لا أستمتع بالأشياء كما كنت من قبل.", "en": "I don't enjoy things the way I used to."},
        {"score": 2, "ar": "لا أحصل على إشباع حقيقي من أي شيء بعد الآن.", "en": "I don't get real satisfaction out of anything anymore."},
        {"score": 3, "ar": "أشعر بعدم الرضا أو الملل من كل شيء.", "en": "I am dissatisfied or bored with everything."},
    ]},
    {"theme_ar": "الشعور بالذنب", "theme_en": "Guilt", "options": [
        {"score": 0, "ar": "لا أشعر بالذنب بصفة خاصة.", "en": "I don't feel particularly guilty."},
        {"score": 1, "ar": "أشعر بالذنب في كثير من الأحيان.", "en": "I feel guilty a good part of the time."},
        {"score": 2, "ar": "أشعر بالذنب معظم الوقت.", "en": "I feel quite guilty most of the time."},
        {"score": 3, "ar": "أشعر بالذنب طوال الوقت.", "en": "I feel guilty all of the time."},
    ]},
    {"theme_ar": "الشعور بالعقاب", "theme_en": "Sense of Punishment", "options": [
        {"score": 0, "ar": "لا أشعر أنني أُعاقَب.", "en": "I don't feel I am being punished."},
        {"score": 1, "ar": "أشعر أنه ربما أُعاقَب.", "en": "I feel I may be punished."},
        {"score": 2, "ar": "أتوقع أن أُعاقَب.", "en": "I expect to be punished."},
        {"score": 3, "ar": "أشعر أنني أُعاقَب.", "en": "I feel I am being punished."},
    ]},
    {"theme_ar": "كره الذات", "theme_en": "Self-Dislike", "options": [
        {"score": 0, "ar": "لا أشعر بخيبة أمل في نفسي.", "en": "I don't feel disappointed in myself."},
        {"score": 1, "ar": "أشعر بخيبة أمل في نفسي.", "en": "I am disappointed in myself."},
        {"score": 2, "ar": "أشعر باشمئزاز من نفسي.", "en": "I am disgusted with myself."},
        {"score": 3, "ar": "أكره نفسي.", "en": "I hate myself."},
    ]},
    {"theme_ar": "لوم الذات", "theme_en": "Self-Accusation", "options": [
        {"score": 0, "ar": "لا أشعر أنني أسوأ من أي شخص آخر.", "en": "I don't feel I am any worse than anybody else."},
        {"score": 1, "ar": "أنتقد نفسي بسبب ضعفي وأخطائي.", "en": "I am critical of myself for my weaknesses or mistakes."},
        {"score": 2, "ar": "أُلوّم نفسي طوال الوقت على عيوبي.", "en": "I blame myself all the time for my faults."},
        {"score": 3, "ar": "أُلوّم نفسي على كل شيء سيئ يحدث.", "en": "I blame myself for everything bad that happens."},
    ]},
    {"theme_ar": "أفكار انتحارية", "theme_en": "Suicidal Ideation", "options": [
        {"score": 0, "ar": "لا تراودني أي أفكار عن قتل نفسي.", "en": "I don't have any thoughts of killing myself."},
        {"score": 1, "ar": "تراودني أفكار عن قتل نفسي لكنني لن أنفذها.", "en": "I have thoughts of killing myself, but I would not carry them out."},
        {"score": 2, "ar": "أريد أن أقتل نفسي.", "en": "I would like to kill myself."},
        {"score": 3, "ar": "سأقتل نفسي لو سنحت لي الفرصة.", "en": "I would like to kill myself if I had the chance."},
    ]},
    {"theme_ar": "البكاء", "theme_en": "Crying", "options": [
        {"score": 0, "ar": "لا أبكي أكثر من المعتاد.", "en": "I don't cry any more than usual."},
        {"score": 1, "ar": "أبكي أكثر مما كنت في السابق.", "en": "I cry more now than I used to."},
        {"score": 2, "ar": "أبكي طوال الوقت الآن.", "en": "I cry all the time now."},
        {"score": 3, "ar": "كنت أستطيع البكاء من قبل لكنني الآن عاجز عنه حتى لو أردت.", "en": "I used to be able to cry, but now I can't cry even though I want to."},
    ]},
    {"theme_ar": "الانفعال والتهيج", "theme_en": "Irritability", "options": [
        {"score": 0, "ar": "لا أكون أكثر انفعالاً من المعتاد.", "en": "I am no more irritated by things than I ever was."},
        {"score": 1, "ar": "أكون أكثر انفعالاً قليلاً مما كنت عليه عادةً.", "en": "I am slightly more irritated now than usual."},
        {"score": 2, "ar": "أشعر بالانزعاج والتهيج كثيراً من الوقت.", "en": "I am quite annoyed or irritated a good deal of the time."},
        {"score": 3, "ar": "أشعر بالتهيج طوال الوقت.", "en": "I feel irritated all the time."},
    ]},
    {"theme_ar": "الانسحاب الاجتماعي", "theme_en": "Social Withdrawal", "options": [
        {"score": 0, "ar": "لم أفقد اهتمامي بالآخرين.", "en": "I have not lost interest in other people."},
        {"score": 1, "ar": "اهتمامي بالآخرين أقل مما كان عليه.", "en": "I am less interested in other people than I used to be."},
        {"score": 2, "ar": "لقد فقدت معظم اهتمامي بالآخرين.", "en": "I have lost most of my interest in other people."},
        {"score": 3, "ar": "لقد فقدت كل اهتمامي بالآخرين.", "en": "I have lost all of my interest in other people."},
    ]},
    {"theme_ar": "التردد في اتخاذ القرار", "theme_en": "Indecisiveness", "options": [
        {"score": 0, "ar": "أتخذ القرارات بنفس الكفاءة التي كنت عليها.", "en": "I make decisions about as well as I ever could."},
        {"score": 1, "ar": "أؤجل اتخاذ القرارات أكثر مما كنت في السابق.", "en": "I put off making decisions more than I used to."},
        {"score": 2, "ar": "أجد صعوبة أكبر في اتخاذ القرارات مقارنةً بالسابق.", "en": "I have greater difficulty in making decisions than before."},
        {"score": 3, "ar": "لا أستطيع اتخاذ أي قرار على الإطلاق بعد الآن.", "en": "I can't make decisions at all anymore."},
    ]},
    {"theme_ar": "صورة الجسم", "theme_en": "Body Image", "options": [
        {"score": 0, "ar": "لا أشعر أن مظهري أسوأ مما كان عليه.", "en": "I don't feel that I look any worse than I used to."},
        {"score": 1, "ar": "أخشى أن أبدو شيخاً أو غير جذاب.", "en": "I am worried that I am looking old or unattractive."},
        {"score": 2, "ar": "أشعر بأن ثمة تغيرات دائمة في مظهري تجعلني أبدو غير جذاب.", "en": "I feel there are permanent changes in my appearance that make me look unattractive."},
        {"score": 3, "ar": "أعتقد أنني أبدو قبيحاً.", "en": "I believe that I look ugly."},
    ]},
    {"theme_ar": "تعطّل القدرة على العمل", "theme_en": "Work Inhibition", "options": [
        {"score": 0, "ar": "أستطيع العمل بنفس الكفاءة تقريباً كما كنت من قبل.", "en": "I can work about as well as before."},
        {"score": 1, "ar": "يتطلب مني البدء في فعل أي شيء جهداً إضافياً.", "en": "It takes an extra effort to get started at doing something."},
        {"score": 2, "ar": "أضطر إلى الدفع الشديد لنفسي لأداء أي شيء.", "en": "I have to push myself very hard to do anything."},
        {"score": 3, "ar": "لا أستطيع إنجاز أي عمل على الإطلاق.", "en": "I can't do any work at all."},
    ]},
    {"theme_ar": "اضطراب النوم", "theme_en": "Sleep Disturbance", "options": [
        {"score": 0, "ar": "أنام بصورة طبيعية.", "en": "I can sleep as well as usual."},
        {"score": 1, "ar": "لا أنام بصورة جيدة كما كنت من قبل.", "en": "I don't sleep as well as I used to."},
        {"score": 2, "ar": "أستيقظ مبكراً بساعة أو ساعتين ويصعب عليّ العودة للنوم.", "en": "I wake up 1-2 hours earlier than usual and find it hard to get back to sleep."},
        {"score": 3, "ar": "أستيقظ مبكراً بعدة ساعات ولا أستطيع العودة للنوم.", "en": "I wake up several hours earlier than I used to and cannot get back to sleep."},
    ]},
    {"theme_ar": "الإجهاد والتعب", "theme_en": "Fatigability", "options": [
        {"score": 0, "ar": "لا أتعب أكثر من المعتاد.", "en": "I don't get more tired than usual."},
        {"score": 1, "ar": "أتعب بسهولة أكبر مما كنت عليه من قبل.", "en": "I get tired more easily than I used to."},
        {"score": 2, "ar": "أتعب من أي شيء تقريباً أفعله.", "en": "I get tired from doing almost anything."},
        {"score": 3, "ar": "أنا منهك للغاية بحيث لا أستطيع فعل أي شيء.", "en": "I am too tired to do anything."},
    ]},
    {"theme_ar": "فقدان الشهية", "theme_en": "Appetite Loss", "options": [
        {"score": 0, "ar": "شهيتي طبيعية كالمعتاد.", "en": "My appetite is no worse than usual."},
        {"score": 1, "ar": "شهيتي ليست جيدة كما كانت من قبل.", "en": "My appetite is not as good as it used to be."},
        {"score": 2, "ar": "شهيتي أسوأ بكثير الآن.", "en": "My appetite is much worse now."},
        {"score": 3, "ar": "لا أشعر بأي شهية على الإطلاق.", "en": "I have no appetite at all anymore."},
    ]},
    {"theme_ar": "فقدان الوزن", "theme_en": "Weight Loss", "options": [
        {"score": 0, "ar": "لم أفقد وزناً يُذكر مؤخراً.", "en": "I haven't lost much weight, if any, lately."},
        {"score": 1, "ar": "فقدت أكثر من خمسة أرطال.", "en": "I have lost more than five pounds."},
        {"score": 2, "ar": "فقدت أكثر من عشرة أرطال.", "en": "I have lost more than ten pounds."},
        {"score": 3, "ar": "فقدت أكثر من خمسة عشر رطلاً.", "en": "I have lost more than fifteen pounds."},
    ]},
    {"theme_ar": "الانشغال بالأمراض الجسدية", "theme_en": "Somatic Preoccupation", "options": [
        {"score": 0, "ar": "لا أكون أكثر قلقاً على صحتي من المعتاد.", "en": "I am no more worried about my health than usual."},
        {"score": 1, "ar": "أشعر بالقلق من مشاكل جسدية كالآلام واضطراب المعدة.", "en": "I am worried about physical problems like aches, pains, or upset stomach."},
        {"score": 2, "ar": "أنا قلق جداً من مشاكل جسدية ويصعب عليّ التفكير في أي شيء آخر.", "en": "I am very worried about physical problems and it's hard to think of much else."},
        {"score": 3, "ar": "أنا قلق جداً من مشاكلي الجسدية لدرجة أنني لا أستطيع التفكير في أي شيء آخر.", "en": "I am so worried about my physical problems that I cannot think of anything else."},
    ]},
    {"theme_ar": "فقدان الرغبة الجنسية", "theme_en": "Loss of Libido", "options": [
        {"score": 0, "ar": "لم ألاحظ أي تغيير في اهتمامي بالجنس مؤخراً.", "en": "I have not noticed any recent change in my interest in sex."},
        {"score": 1, "ar": "اهتمامي بالجنس أقل مما كان عليه من قبل.", "en": "I am less interested in sex than I used to be."},
        {"score": 2, "ar": "اهتمامي بالجنس شبه معدوم الآن.", "en": "I have almost no interest in sex."},
        {"score": 3, "ar": "فقدت الاهتمام بالجنس كلياً.", "en": "I have lost interest in sex completely."},
    ]},
]

def calculate_score(answers):
    return sum(v["score"] for v in answers.values())

def get_severity_level(total):
    if total <= 10:   return {"label": "Normal / Minimal",              "range": "1-10",  "color": "#4CAF50"}
    elif total <= 16: return {"label": "Mild Mood Disturbance",          "range": "11-16", "color": "#8BC34A"}
    elif total <= 20: return {"label": "Borderline Clinical Depression", "range": "17-20", "color": "#FFC107"}
    elif total <= 30: return {"label": "Moderate Depression",            "range": "21-30", "color": "#FF9800"}
    elif total <= 40: return {"label": "Severe Depression",              "range": "31-40", "color": "#F44336"}
    else:             return {"label": "Extreme Depression",             "range": "40+",   "color": "#B71C1C"}

def get_score_breakdown(answers):
    COGNITIVE = [1, 2, 3, 5, 6, 7, 8, 12, 13]
    AFFECTIVE = [0, 4, 9, 10, 11]
    SOMATIC   = [14, 15, 16, 17, 18, 19, 20]
    def sub(indices): return sum(answers[i]["score"] for i in indices if i in answers)
    return {
        "cognitive_score":         sub(COGNITIVE),
        "affective_score":         sub(AFFECTIVE),
        "somatic_score":           sub(SOMATIC),
        "flagged_items":           [answers[i]["theme_en"] for i in answers if answers[i]["score"] >= 2],
        "suicidal_ideation_score": answers.get(8, {}).get("score", 0),
        "item_detail": [
            {"number": i+1, "theme": answers[i]["theme_en"],
             "score": answers[i]["score"], "response": answers[i]["text_en"]}
            for i in sorted(answers.keys())
        ],
    }

def generate_report(client_name, total_score, severity, breakdown, answers):
    item_lines = "\n".join(
        f"  Q{item['number']} ({item['theme']}): Score {item['score']} - \"{item['response']}\""
        for item in breakdown["item_detail"]
    )
    si_note = ""
    if breakdown["suicidal_ideation_score"] >= 1:
        si_note = (f"\nIMPORTANT: The client endorsed suicidal ideation at level "
                   f"{breakdown['suicidal_ideation_score']} on item 9. "
                   f"This requires explicit risk assessment discussion in the report.")
    prompt = f"""You are a licensed clinical psychologist writing a confidential professional assessment report.

CLIENT: {client_name}
ASSESSMENT: Beck Depression Inventory (BDI-II)
TOTAL SCORE: {total_score} / 63
SEVERITY: {severity['label']} (Range: {severity['range']})

DOMAIN SUB-SCORES:
  Cognitive cluster: {breakdown['cognitive_score']}
  Affective cluster: {breakdown['affective_score']}
  Somatic cluster:   {breakdown['somatic_score']}

FLAGGED ITEMS (score 2 or above): {', '.join(breakdown['flagged_items']) if breakdown['flagged_items'] else 'None'}
{si_note}

ITEM-BY-ITEM RESPONSES:
{item_lines}

Write a full professional psychotherapy assessment report with these sections:
1. REFERRAL AND ASSESSMENT OVERVIEW
2. PRESENTING PROFILE
3. DOMAIN ANALYSIS (Cognitive / Affective / Somatic)
4. ITEM-LEVEL CLINICAL OBSERVATIONS (highlight items scoring 2 or above; address suicidal ideation separately if endorsed)
5. RISK CONSIDERATIONS
6. CLINICAL FORMULATION
7. TREATMENT RECOMMENDATIONS
8. SUMMARY

Use formal clinical language. Reference actual scores and responses. Ready to place in a clinical file."""

    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from Streamlit secrets.")
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 2000, "temperature": 0.4},
        timeout=60,
    )
    if not response.ok:
        try:    error_detail = response.json()
        except: error_detail = response.text
        raise Exception(f"Groq API error {response.status_code}: {error_detail}")
    return response.json()["choices"][0]["message"]["content"].strip()

def create_pdf_report(path, client_name, total_score, severity, report_text, answers, timestamp):
    DARK=colors.HexColor("#1C1917"); WARM=colors.HexColor("#8B7355")
    ACCENT=colors.HexColor("#C4956A"); LIGHT_BG=colors.HexColor("#F7F3EE")
    BORDER=colors.HexColor("#DDD5C8"); RED_FLAG=colors.HexColor("#B71C1C")

    def sev_color(label):
        for k,c in [("Normal","#4CAF50"),("Mild","#8BC34A"),("Borderline","#FFC107"),
                    ("Moderate","#FF9800"),("Severe","#F44336"),("Extreme","#B71C1C")]:
            if k.lower() in label.lower(): return colors.HexColor(c)
        return ACCENT

    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    title_s  = ParagraphStyle("T",  fontName="Times-Roman",      fontSize=22, textColor=DARK, alignment=TA_CENTER, spaceAfter=4)
    sub_s    = ParagraphStyle("S",  fontName="Times-Italic",      fontSize=11, textColor=WARM, alignment=TA_CENTER, spaceAfter=2)
    meta_s   = ParagraphStyle("M",  fontName="Helvetica",         fontSize=8,  textColor=WARM, alignment=TA_CENTER, spaceAfter=14)
    sec_s    = ParagraphStyle("Se", fontName="Helvetica-Bold",    fontSize=10, textColor=WARM, spaceBefore=14, spaceAfter=4)
    body_s   = ParagraphStyle("B",  fontName="Helvetica",         fontSize=9.5,textColor=DARK, leading=15, spaceAfter=6)
    small_s  = ParagraphStyle("Sm", fontName="Helvetica",         fontSize=8.5,textColor=WARM, leading=13)
    flag_s   = ParagraphStyle("F",  fontName="Helvetica-Bold",    fontSize=9.5,textColor=RED_FLAG, leading=14)
    footer_s = ParagraphStyle("Ft", fontName="Helvetica-Oblique", fontSize=7.5,textColor=WARM, leading=11, alignment=TA_CENTER)

    story = []
    date_str = datetime.datetime.now().strftime("%B %d, %Y  |  %H:%M")

    if os.path.exists(LOGO_FILE):
        try:
            logo = RLImage(LOGO_FILE, width=4*cm, height=2*cm)
            logo.hAlign = "CENTER"
            story.append(logo); story.append(Spacer(1, 0.3*cm))
        except: pass

    story += [Paragraph("Beck Depression Inventory", title_s), Spacer(1,0.3*cm),
              Paragraph("Clinical Assessment Report", sub_s),
              Paragraph(f"CONFIDENTIAL  ·  {date_str}", meta_s),
              HRFlowable(width="100%", thickness=1, color=BORDER), Spacer(1,0.4*cm)]

    # Fixed bar
    bar_filled = max(0, min(30, int((total_score / 63) * 30)))
    hex_sev = severity["color"].lstrip("#")
    info_data = [
        [Paragraph("<b>Client</b>", small_s), Paragraph(client_name, body_s),
         Paragraph("<b>Total Score</b>", small_s), Paragraph(f"<b>{total_score} / 63</b>", body_s)],
        [Paragraph("<b>Assessment</b>", small_s), Paragraph("BDI-II", body_s),
         Paragraph("<b>Severity</b>", small_s),
         Paragraph(f"<b>{severity['label']}</b>",
                   ParagraphStyle("SL", fontName="Helvetica-Bold", fontSize=9.5, textColor=sev_color(severity['label'])))],
        [Paragraph("<b>Score Bar</b>", small_s),
         Paragraph(f'<font color="#{hex_sev}">{"█"*bar_filled}</font><font color="#CCCCCC">{"░"*(30-bar_filled)}</font>',
                   ParagraphStyle("BR", fontName="Courier", fontSize=8, leading=12)),
         Paragraph("<b>Range</b>", small_s), Paragraph(severity["range"], body_s)],
    ]
    info_t = Table(info_data, colWidths=[3*cm, 6.5*cm, 3*cm, 4.5*cm])
    info_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),LIGHT_BG),("BOX",(0,0),(-1,-1),0.5,BORDER),
        ("INNERGRID",(0,0),(-1,-1),0.3,BORDER),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),("LEFTPADDING",(0,0),(-1,-1),10),
    ]))
    story += [info_t, Spacer(1,0.5*cm)]

    story += [Paragraph("ITEM RESPONSES", sec_s),
              HRFlowable(width="100%", thickness=0.5, color=BORDER), Spacer(1,0.2*cm)]

    rows = [[Paragraph("<b>#</b>",small_s), Paragraph("<b>Domain</b>",small_s),
             Paragraph("<b>Response Selected</b>",small_s), Paragraph("<b>Score</b>",small_s)]]
    for i in sorted(answers.keys()):
        a=answers[i]; sv=a["score"]
        rows.append([
            Paragraph(str(i+1), small_s),
            Paragraph(a["theme_en"], small_s),
            Paragraph(a["text_en"], ParagraphStyle("RC",fontName="Helvetica",fontSize=8.5,textColor=DARK,leading=12)),
            Paragraph(f"<b>{sv}</b>", ParagraphStyle("SC",fontName="Helvetica-Bold",fontSize=9,
                      textColor=RED_FLAG if sv>=2 else DARK,alignment=TA_CENTER)),
        ])
    tstyle = [
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EDE9E3")),
        ("BOX",(0,0),(-1,-1),0.5,BORDER),("INNERGRID",(0,0),(-1,-1),0.3,BORDER),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),("ALIGN",(3,0),(3,-1),"CENTER"),
    ]
    for row_idx, i in enumerate(sorted(answers.keys()), start=1):
        if answers[i]["score"] >= 2:
            tstyle.append(("BACKGROUND",(0,row_idx),(-1,row_idx),colors.HexColor("#FFF3F3")))
    t = Table(rows, colWidths=[1*cm,3.5*cm,11*cm,1.5*cm])
    t.setStyle(TableStyle(tstyle))
    story += [t, Spacer(1,0.5*cm)]

    story += [HRFlowable(width="100%",thickness=1,color=BORDER), Spacer(1,0.3*cm),
              Paragraph("CLINICAL REPORT", sec_s),
              HRFlowable(width="100%",thickness=0.5,color=BORDER), Spacer(1,0.2*cm)]
    for line in report_text.split("\n"):
        line = line.strip()
        if not line: story.append(Spacer(1,0.2*cm))
        elif line.isupper() or (line.endswith(":") and len(line)<60): story.append(Paragraph(line,sec_s))
        elif "suicidal" in line.lower(): story.append(Paragraph(line,flag_s))
        else: story.append(Paragraph(line,body_s))

    story += [Spacer(1,0.6*cm), HRFlowable(width="100%",thickness=0.5,color=BORDER), Spacer(1,0.2*cm),
              Paragraph("This report is strictly confidential and intended solely for the treating clinician. "
                        "It is not to be shared with the client or any third party without explicit written consent. "
                        "AI-assisted analysis should be reviewed in conjunction with clinical judgment.", footer_s)]
    doc.build(story)

def send_report_email(pdf_path, client_name, total_score, severity, filename):
    date_str = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")
    msg = MIMEMultipart("mixed")
    msg["From"]=GMAIL_ADDRESS; msg["To"]=THERAPIST_EMAIL
    msg["Subject"]=f"[BDI Report] {client_name} — {severity['label']} (Score: {total_score}/63) — {date_str}"
    body_html = f"""<html><body style="font-family:Georgia,serif;color:#1C1917;background:#F7F3EE;padding:24px;">
      <div style="max-width:560px;margin:0 auto;background:white;border:1px solid #DDD5C8;border-radius:4px;padding:32px;">
        <h2 style="font-weight:300;font-size:22px;margin-bottom:4px;">Beck Depression Inventory</h2>
        <p style="color:#8B7355;font-size:12px;letter-spacing:.08em;text-transform:uppercase;margin-top:0;">New Assessment Submitted</p>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:20px 0;">
        <table style="width:100%;font-size:14px;border-collapse:collapse;">
          <tr><td style="padding:8px 0;color:#8B7355;width:40%;">Client</td><td><strong>{client_name}</strong></td></tr>
          <tr><td style="padding:8px 0;color:#8B7355;">Date &amp; Time</td><td>{date_str}</td></tr>
          <tr><td style="padding:8px 0;color:#8B7355;">Total Score</td><td><strong>{total_score} / 63</strong></td></tr>
          <tr><td style="padding:8px 0;color:#8B7355;">Severity</td>
              <td><strong style="color:{severity['color']};">{severity['label']}</strong></td></tr>
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:20px 0;">
        <p style="font-size:13px;line-height:1.6;">Full clinical report attached as PDF.</p>
        <p style="font-size:11px;color:#8B7355;margin-top:24px;font-style:italic;">Confidential — intended only for the treating clinician.</p>
      </div></body></html>"""
    msg.attach(MIMEText(body_html, "html"))
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application","octet-stream"); part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, THERAPIST_EMAIL, msg.as_string())

st.set_page_config(page_title="تقييم الاكتئاب", page_icon="🧠",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=Jost:wght@300;400;500&display=swap');
:root{--cream:#F7F3EE;--deep:#1C1917;--warm:#8B7355;--accent:#C4956A;--border:#DDD5C8;--selected:#2D2926;}
#MainMenu{visibility:hidden!important;display:none!important;}
header[data-testid="stHeader"]{visibility:hidden!important;display:none!important;}
footer{visibility:hidden!important;display:none!important;}
[data-testid="stToolbar"]{display:none!important;}
[data-testid="stDecoration"]{display:none!important;}
[data-testid="stStatusWidget"]{display:none!important;}
[data-testid="stActionButton"]{display:none!important;}
a[href*="streamlit.io"]{display:none!important;}
[class*="viewerBadge"]{display:none!important;}
[class*="ProfileBadge"]{display:none!important;}
html,body,[data-theme="dark"],[data-theme="light"]{color-scheme:light only!important;}
[data-testid="stAppViewContainer"],.stApp{background-color:#F7F3EE!important;color:#1C1917!important;}
html,body,[class*="css"]{font-family:'Jost',sans-serif;background-color:var(--cream);color:var(--deep);direction:rtl;}
.stApp{background-color:var(--cream);}
.assessment-header{text-align:center;padding:3rem 0 2rem 0;border-bottom:1px solid var(--border);margin-bottom:2.5rem;direction:rtl;}
.assessment-header h1{font-family:'Cormorant Garamond',serif;font-size:2.4rem;font-weight:300;letter-spacing:.02em;margin-bottom:.4rem;}
.assessment-header p{color:var(--warm);font-size:.85rem;font-weight:300;letter-spacing:.06em;}
.question-block{background:white;border:1px solid var(--border);border-radius:4px;padding:1.8rem 2rem;margin-bottom:1.2rem;transition:border-color .2s ease;direction:rtl;text-align:right;}
.question-block:hover{border-color:var(--accent);}
.question-number{font-size:.72rem;font-weight:500;letter-spacing:.08em;color:var(--accent);margin-bottom:.5rem;}
.question-text{font-family:'Cormorant Garamond',serif;font-size:1.15rem;font-weight:400;color:var(--deep);margin-bottom:1.2rem;line-height:1.6;}
div[data-testid="stRadio"]>label{display:none;}
div[data-testid="stRadio"]>div{gap:.5rem!important;flex-direction:column!important;}
div[data-testid="stRadio"]>div>label{background:var(--cream)!important;border:1px solid var(--border)!important;border-radius:20px!important;padding:.6rem 1rem!important;cursor:pointer!important;transition:all .15s ease!important;font-size:.88rem!important;color:var(--deep)!important;font-family:'Jost',sans-serif!important;width:100%!important;text-align:right!important;direction:rtl!important;}
div[data-testid="stRadio"]>div>label:hover{border-color:var(--accent)!important;background:#FDF9F4!important;}
.progress-bar-wrapper{background:var(--border);border-radius:2px;height:3px;margin-bottom:2rem;}
.progress-bar-fill{height:3px;border-radius:2px;background:linear-gradient(90deg,var(--warm),var(--accent));}
.stButton>button{background:var(--selected)!important;color:var(--cream)!important;border:none!important;padding:.85rem 3rem!important;font-family:'Jost',sans-serif!important;font-size:.85rem!important;font-weight:400!important;letter-spacing:.08em!important;border-radius:2px!important;transition:background .2s ease!important;}
.stButton>button:hover{background:var(--warm)!important;}
.thank-you-block{text-align:center;padding:5rem 2rem;direction:rtl;}
.thank-you-block h2{font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:300;margin-bottom:1rem;}
.thank-you-block p{color:var(--warm);font-size:.95rem;font-weight:300;max-width:400px;margin:0 auto;line-height:1.9;}
div[data-testid="stTextInput"] input{background:white!important;border:1px solid var(--border)!important;border-radius:3px!important;font-family:'Jost',sans-serif!important;color:var(--deep)!important;}
</style>""", unsafe_allow_html=True)

page = st.query_params.get("page", "client")

if page == "admin":
    st.markdown('<div class="assessment-header"><p>بوابة المعالج</p><h1>التقارير المحفوظة</h1></div>', unsafe_allow_html=True)
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    if not st.session_state.admin_authenticated:
        pwd = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        if st.button("دخول"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state.admin_authenticated = True; st.rerun()
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
                with col1: st.markdown(f"📄 `{fname}`")
                with col2:
                    with open(os.path.join(reports_dir, fname), "rb") as f:
                        st.download_button("تحميل", data=f, file_name=fname, mime="application/pdf", key=fname)
        if st.button("تسجيل الخروج"):
            st.session_state.admin_authenticated = False; st.rerun()

else:
    if "submitted"      not in st.session_state: st.session_state.submitted = False
    if "access_granted" not in st.session_state: st.session_state.access_granted = False

    # ── Access code gate ───────────────────────────────────────
    if not st.session_state.access_granted:
        if os.path.exists(LOGO_FILE):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2: st.image(LOGO_FILE, use_container_width=True)
        st.markdown("""<div class="assessment-header">
            <p>تقييم نفسي سري</p>
            <h1>مقياس بيك للاكتئاب</h1>
        </div>""", unsafe_allow_html=True)
        st.markdown("""<div style="max-width:360px;margin:0 auto;padding:2rem 0;text-align:center;direction:rtl;">
            <p style="color:#8B7355;font-size:.9rem;margin-bottom:1.5rem;line-height:1.8;">
                هذا التقييم متاح للمرضى المحالين فقط.<br>
                يرجى إدخال رمز الوصول الذي زوّدك به معالجك.
            </p>
        </div>""", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            code = st.text_input("رمز الوصول", type="password",
                                 placeholder="أدخل رمز الوصول",
                                 label_visibility="collapsed")
            if st.button("دخول", use_container_width=True):
                if code == st.secrets.get("ACCESS_CODE", ""):
                    st.session_state.access_granted = True
                    st.rerun()
                else:
                    st.markdown("""<div style="background:#FFF0F0;border-right:3px solid #D9534F;
                        border-left:none;padding:.8rem 1rem;border-radius:4px 0 0 4px;
                        font-size:.88rem;color:#7A1A1A;margin:.5rem 0;
                        direction:rtl;text-align:right;">
                        &#9888; رمز الوصول غير صحيح. يرجى المراجعة والمحاولة مرة أخرى.
                    </div>""", unsafe_allow_html=True)
        st.stop()

    if st.session_state.submitted:
        st.markdown('<div class="thank-you-block"><h2>شكراً لك</h2><p>تم تسليم إجاباتك بنجاح.<br>سيتواصل معك المعالج في أقرب وقت.</p></div>', unsafe_allow_html=True)
        if st.session_state.get("email_error"):
            st.warning(f"ملاحظة: فشل إرسال البريد — {st.session_state.email_error}")
    else:
        if os.path.exists(LOGO_FILE):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2: st.image(LOGO_FILE, use_container_width=True)

        st.markdown('<div class="assessment-header"><p>تقييم نفسي سري</p><h1>مقياس بيك للاكتئاب</h1></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:.88rem;color:#8B7355;text-align:center;margin-bottom:2rem;font-weight:300;line-height:1.9;direction:rtl;">اقرأ كل مجموعة من العبارات بعناية، ثم اختر العبارة التي تصف بشكل أفضل<br><strong>كيف كنت تشعر خلال الأسبوعين الماضيين</strong>، بما في ذلك اليوم.</p>', unsafe_allow_html=True)

        client_name = st.text_input("اسمك باللغة الإنجليزية (اختياري)", placeholder="Your name in English")
        st.markdown("<br>", unsafe_allow_html=True)

        answers = {}
        all_answered = True

        for i, q in enumerate(BDI_QUESTIONS):
            st.markdown(f'<div class="question-block"><div class="question-number">السؤال {i+1} من {len(BDI_QUESTIONS)}</div><div class="question-text">{q["theme_ar"]}</div></div>', unsafe_allow_html=True)
            options_ar = [opt["ar"] for opt in q["options"]]
            choice = st.radio(label=f"q_{i}", options=options_ar, index=None, key=f"q_{i}", label_visibility="collapsed")
            if choice is None:
                all_answered = False
            else:
                opt = next(o for o in q["options"] if o["ar"] == choice)
                answers[i] = {"score": opt["score"], "text_en": opt["en"], "theme_en": q["theme_en"]}

        answered_count = len(answers)
        pct = int((answered_count / len(BDI_QUESTIONS)) * 100)
        st.markdown(f'<div style="text-align:center;margin:1.5rem 0 .5rem 0;font-size:.78rem;color:#8B7355;letter-spacing:.05em;direction:rtl;">{answered_count} من {len(BDI_QUESTIONS)} سؤالاً تمت الإجابة عنه</div><div class="progress-bar-wrapper"><div class="progress-bar-fill" style="width:{pct}%"></div></div>', unsafe_allow_html=True)

        if not all_answered and answered_count > 0:
            st.markdown('<div style="background:#FFF8F0;border-right:3px solid #E07B39;border-left:none;padding:1rem 1.2rem;border-radius:4px 0 0 4px;font-size:.88rem;color:#7A3D1A;margin:1rem 0;direction:rtl;text-align:right;">⚠ يرجى الإجابة على جميع الأسئلة قبل التسليم.</div>', unsafe_allow_html=True)

        has_arabic_name = any('\u0600' <= c <= '\u06ff' for c in (client_name or ""))

        st.markdown('<div style="text-align:center;padding:2rem 0 3rem 0;">', unsafe_allow_html=True)
        submit = st.button("تسليم الاختبار", disabled=not all_answered)
        st.markdown('</div>', unsafe_allow_html=True)

        if submit and has_arabic_name:
            st.markdown('<div style="background:#FFF0F0;border-right:3px solid #D9534F;border-left:none;padding:1rem 1.2rem;border-radius:4px 0 0 4px;font-size:.92rem;color:#7A1A1A;margin:.5rem 0;direction:rtl;text-align:right;font-weight:500;">⚠ يرجى كتابة اسمك باللغة الإنجليزية فقط. الأسماء المكتوبة بالعربية غير مقبولة.</div>', unsafe_allow_html=True)

        if submit and all_answered and not has_arabic_name:
            with st.spinner("جاري تسليم إجاباتك..."):
                total_score = calculate_score(answers)
                severity    = get_severity_level(total_score)
                breakdown   = get_score_breakdown(answers)
                report_text = generate_report(client_name or "Anonymous", total_score, severity, breakdown, answers)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = (client_name or "anonymous").replace(" ", "_").lower()
                filename  = f"BDI_{safe_name}_{timestamp}.pdf"
                os.makedirs("reports", exist_ok=True)
                pdf_path  = os.path.join("reports", filename)

                try:
                    create_pdf_report(pdf_path, client_name or "Anonymous",
                                      total_score, severity, report_text, answers, timestamp)
                except Exception as pdf_err:
                    st.error(f"خطأ في إنشاء التقرير: {pdf_err}"); st.stop()

                email_error = None
                try:
                    send_report_email(pdf_path, client_name or "Anonymous", total_score, severity, filename)
                except Exception as e:
                    email_error = str(e)

                st.session_state.submitted   = True
                st.session_state.email_error = email_error
                st.rerun()
