"""סיווג חכם של טקסט למשימה באמצעות Claude API.

מקבל טקסט חופשי (אימייל, הודעה, וכו') ומחזיר:
- קטגוריה (moked / council_site / crm)
- רמת דחיפות (low / medium / high / urgent)
- תאריך יעד (אם מצוין בטקסט)
- בעלים (self / riki - רלוונטי בעיקר במוקד)
- ציון ביטחון של המודל בסיווג
"""

import json
import anthropic
from datetime import date


# המודל בו נשתמש - Haiku 4.5: מהיר, זול, מספיק חכם לסיווג
MODEL = "claude-haiku-4-5-20251001"

CLASSIFY_PROMPT = """אתה עוזר אישי של מנהלת מחלקת שירות בעירייה.
היא אחראית על חמישה תחומים, ואתה צריך לעזור לה לסווג משימות נכנסות.

הקטגוריות:
1. **crm** - פרויקט CRM: מסד נתוני תושבים, דוחות, אינטגרציות בין מערכות, ניהול מידע, אוטומציה.
2. **council_site** - פרויקט אתר עירייה: תוכן באתר, באגים, עיצוב, פיתוח אתר, הודעות לציבור, הנגשה.
3. **service_processes** - פרויקט תהליכי שירות: שיפור תהליכים, ייעול נהלים, מיפוי תהליכים, אופטימיזציה.
4. **moked** - מוקד 106: פניות תושבים, תלונות, אירועי שטח, מענה לציבור, תקלות דחופות.
5. **routine** - משימות שוטפות: ניהול שוטף, פגישות, מעקבים, משימות אדמיניסטרטיביות שלא נכנסות לפרויקט ספציפי.

חוקים:
- "ריקי" היא הסגנית. היא אחראית **רק** על מוקד 106. אם הטקסט מזכיר את ריקי ביחס למשימה - owner = "riki", אחרת "self".
- דחיפות: urgent (היום/מיידי), high (תוך יומיים), medium (תוך שבוע), low (פחות דחוף).
- תאריך יעד: חלץ אם מוזכר במפורש או משתמע (למשל "עד יום ראשון", "בסוף החודש"). אם לא ברור - null.
- אם הסיווג לא ברור - תן confidence נמוך.

תאריך נוכחי לחישובים: {today}

הטקסט לסיווג:
---
{text}
---

החזר JSON בלבד (ללא markdown, ללא הסברים מסביב):
{{
  "category": "crm" | "council_site" | "service_processes" | "moked" | "routine",
  "priority": "low" | "medium" | "high" | "urgent",
  "due_date": "YYYY-MM-DD" or null,
  "owner": "self" | "riki",
  "confidence": 0.0 to 1.0,
  "suggested_title": "כותרת קצרה ותמציתית בעברית (עד 80 תווים)",
  "reasoning": "הסבר קצר בעברית למה בחרת ככה (משפט אחד)"
}}"""


def classify_text(text: str, api_key: str) -> dict:
    """שולח טקסט ל-Claude ומחזיר סיווג מובנה."""
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[
            {
                "role": "user",
                "content": CLASSIFY_PROMPT.format(
                    text=text.strip(),
                    today=date.today().isoformat(),
                ),
            }
        ],
    )

    raw = response.content[0].text.strip()

    # חילוץ ה-JSON מהתשובה
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"לא נמצא JSON תקין בתשובה: {raw[:200]}")

    parsed = json.loads(raw[start:end])

    # ולידציה
    required = {"category", "priority", "owner", "confidence", "suggested_title"}
    missing = required - set(parsed.keys())
    if missing:
        raise ValueError(f"חסרים שדות בתשובה: {missing}")

    valid_categories = ("crm", "council_site", "service_processes", "moked", "routine")
    if parsed["category"] not in valid_categories:
        raise ValueError(f"קטגוריה לא חוקית: {parsed['category']}")
    if parsed["priority"] not in ("low", "medium", "high", "urgent"):
        parsed["priority"] = "medium"
    if parsed["owner"] not in ("self", "riki"):
        parsed["owner"] = "self"
    # ריקי רק במוקד
    if parsed["category"] != "moked":
        parsed["owner"] = "self"

    return parsed
