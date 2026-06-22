"""מודל נתונים למשימות - קטגוריות, דחיפות, תאריכי יעד."""

from datetime import datetime, date, timedelta
import uuid


# === קטגוריות ===
CATEGORIES = ["crm", "council_site", "service_processes", "moked", "routine"]
CATEGORY_LABELS = {
    "crm": "פרויקט CRM",
    "council_site": "פרויקט אתר עירייה",
    "service_processes": "פרויקט תהליכי שירות",
    "moked": "מוקד 106",
    "routine": "משימות שוטפות",
}
CATEGORY_ICONS = {
    "crm": "💼",
    "council_site": "🌐",
    "service_processes": "🔄",
    "moked": "📞",
    "routine": "📋",
}

# === בעלי משימות (רלוונטי בעיקר למוקד - אני / ריקי) ===
OWNERS = ["self", "riki"]
OWNER_LABELS = {
    "self": "המשימות שלי",
    "riki": "המשימות של ריקי",
}

# === רמות דחיפות ===
PRIORITIES = ["low", "medium", "high", "urgent"]
PRIORITY_LABELS = {
    "low": "נמוכה",
    "medium": "בינונית",
    "high": "גבוהה",
    "urgent": "דחוף",
}
PRIORITY_ICONS = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
    "urgent": "⚡",
}
PRIORITY_COLORS = {
    "low": "#16a34a",
    "medium": "#ca8a04",
    "high": "#ea580c",
    "urgent": "#dc2626",
}
PRIORITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3, "urgent": 4}

# סף ימים להתראת "דד-ליין מתקרב"
DUE_SOON_DAYS = 2


def new_task(
    title: str,
    category: str,
    priority: str = "medium",
    due_date=None,
    owner: str = "self",
    description: str = "",
    source: str = "manual",
) -> dict:
    """יצירת משימה חדשה עם ברירות מחדל סבירות."""
    now = datetime.now().isoformat()
    return {
        "id": str(uuid.uuid4()),
        "title": title.strip(),
        "description": description.strip(),
        "category": category,
        "owner": owner,
        "priority": priority,
        "due_date": _date_to_iso(due_date),
        "archived": False,
        "completed_at": None,
        "created_at": now,
        "updated_at": now,
        "source": source,  # 'manual' או 'outlook'
    }


def update_task(task: dict, **changes) -> dict:
    """עדכון משימה - מחזיר עותק עם השינויים."""
    updated = dict(task)
    for key, value in changes.items():
        if key == "due_date":
            updated[key] = _date_to_iso(value)
        elif key in updated:
            updated[key] = value
    updated["updated_at"] = datetime.now().isoformat()
    return updated


def complete_and_archive(task: dict) -> dict:
    """סימון משימה כהושלמה והעברה לארכיון."""
    updated = dict(task)
    updated["archived"] = True
    updated["completed_at"] = datetime.now().isoformat()
    updated["updated_at"] = datetime.now().isoformat()
    return updated


def restore_from_archive(task: dict) -> dict:
    """החזרה מארכיון למשימות פעילות."""
    updated = dict(task)
    updated["archived"] = False
    updated["completed_at"] = None
    updated["updated_at"] = datetime.now().isoformat()
    return updated


def _date_to_iso(d):
    """המרת date/datetime/string ל-ISO date או None."""
    if d is None or d == "":
        return None
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    return None


def parse_due_date(task: dict):
    """החזרת תאריך יעד כ-date או None."""
    if not task.get("due_date"):
        return None
    try:
        return date.fromisoformat(task["due_date"])
    except (ValueError, TypeError):
        return None


def is_overdue(task: dict) -> bool:
    """האם המשימה באיחור (תאריך יעד עבר ולא הושלמה)."""
    if task.get("archived"):
        return False
    due = parse_due_date(task)
    return due is not None and due < date.today()


def is_due_soon(task: dict, days: int = DUE_SOON_DAYS) -> bool:
    """האם תאריך היעד מתקרב (תוך X ימים)."""
    if task.get("archived"):
        return False
    due = parse_due_date(task)
    if due is None:
        return False
    today = date.today()
    return today <= due <= today + timedelta(days=days)


def days_until_due(task: dict):
    """כמה ימים נשארו עד תאריך היעד (שלילי = איחור)."""
    due = parse_due_date(task)
    if due is None:
        return None
    return (due - date.today()).days


def sort_key(task: dict):
    """מיון חכם: באיחור ראשון, אחר כך לפי דחיפות, אחר כך לפי תאריך."""
    overdue_flag = 0 if is_overdue(task) else 1
    prio = -PRIORITY_WEIGHTS.get(task.get("priority", "medium"), 2)
    due = parse_due_date(task) or date.max
    return (overdue_flag, prio, due)


# ============================================================
# יומן שיחות (Call log)
# ============================================================
def new_call(
    category: str,
    contact_name: str,
    call_date,
    topic: str,
    notes: str = "",
) -> dict:
    """יצירת רישום שיחה חדש."""
    return {
        "id": str(uuid.uuid4()),
        "category": category,
        "contact_name": contact_name.strip(),
        "date": _date_to_iso(call_date),
        "topic": topic.strip(),
        "notes": notes.strip(),
        "created_at": datetime.now().isoformat(),
    }
