"""
מערכת ניהול משימות - מועצה
============================
3 קטגוריות: מוקד, אתר המועצה, מערכת CRM
+ תת-טבלה לריקי תחת מוקד
+ דשבורד, התראות יומיים לפני, ארכיון
"""

import streamlit as st
from datetime import date, timedelta
import pandas as pd

from models import (
    new_task, update_task, complete_and_archive, restore_from_archive,
    is_overdue, is_due_soon, days_until_due, sort_key,
    CATEGORIES, CATEGORY_LABELS, CATEGORY_ICONS,
    OWNERS, OWNER_LABELS,
    PRIORITIES, PRIORITY_LABELS, PRIORITY_ICONS, PRIORITY_COLORS, PRIORITY_WEIGHTS,
    DUE_SOON_DAYS,
    new_call,
)
from storage import GitHubStorage
from ai_classifier import classify_text


# ============================================================
# הגדרות עמוד + CSS ל-RTL
# ============================================================
st.set_page_config(
    page_title="ניהול משימות - מועצה",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
    /* === RTL וגופן === */
    .stApp, section[data-testid="stSidebar"] { direction: rtl; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div, .stDateInput input {
        text-align: right;
    }
    .stApp, .stMarkdown, button, h1, h2, h3, h4, h5 {
        font-family: 'Rubik', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* === רקעים בגוון קרם === */
    .stApp { background-color: #faf6f0; }
    section[data-testid="stSidebar"] { background-color: #f5ede0; }
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #f5ede0;
    }

    /* === כותרות בחום עמוק === */
    h1, h2, h3, h4, h5 {
        color: #3d2f24 !important;
        font-family: 'Rubik', sans-serif !important;
        font-weight: 600 !important;
    }

    /* === כרטיסי משימות === */
    .task-card {
        background: #ffffff;
        border: 0.5px solid #e8dfd1;
        border-right: 4px solid #b3a899;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .task-card:hover {
        transform: translateX(-2px);
        box-shadow: 0 2px 8px rgba(61, 47, 36, 0.06);
    }
    .task-card.overdue {
        background: #fdf0e8;
        border-right-color: #b54a30;
    }
    .task-card.due-soon {
        background: #fdf5e8;
        border-right-color: #d6a35c;
    }
    .task-card.priority-urgent { border-right-color: #b54a30; }
    .task-card.priority-high { border-right-color: #d68563; }
    .task-card.priority-medium { border-right-color: #c89f5f; }
    .task-card.priority-low { border-right-color: #84a59d; }

    /* === כרטיסי שיחות (ירוק זית) === */
    .call-card {
        background: #ffffff;
        border: 0.5px solid #e8dfd1;
        border-right: 4px solid #84a59d;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .call-card:hover {
        transform: translateX(-2px);
        box-shadow: 0 2px 8px rgba(61, 47, 36, 0.06);
    }

    .task-title {
        font-size: 1.05em;
        font-weight: 600;
        color: #3d2f24;
    }
    .task-meta {
        font-size: 0.85em;
        color: #8a7a6c;
        margin-top: 4px;
    }

    /* === תגיות תאריך - בצורת גלולה === */
    .due-badge-overdue {
        background: #b54a30;
        color: white;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 0.8em;
        font-weight: 500;
        display: inline-block;
    }
    .due-badge-soon {
        background: #d6a35c;
        color: white;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 0.8em;
        font-weight: 500;
        display: inline-block;
    }
    .due-badge-ok {
        background: #ebe2d1;
        color: #6b5a48;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 0.8em;
        display: inline-block;
    }

    /* === מטריקות (מספרים בדשבורד) === */
    [data-testid="stMetricValue"] {
        color: #d68563 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8a7a6c !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetric"] {
        background: white;
        border: 0.5px solid #e8dfd1;
        border-radius: 10px;
        padding: 12px 16px;
    }

    /* === כפתורים === */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease;
    }
    .stButton button[kind="primary"] {
        background-color: #d68563 !important;
        color: white !important;
        border: none !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #c0704d !important;
        transform: translateY(-1px);
    }
    .stButton button[kind="secondary"] {
        background-color: white !important;
        color: #3d2f24 !important;
        border: 1px solid #e8dfd1 !important;
    }
    .stButton button[kind="secondary"]:hover {
        background-color: #f5ede0 !important;
        border-color: #d68563 !important;
        color: #3d2f24 !important;
    }

    /* === שדות קלט === */
    .stTextInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"], .stDateInput input {
        border-radius: 8px !important;
        border-color: #e8dfd1 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #d68563 !important;
        box-shadow: 0 0 0 2px rgba(214, 133, 99, 0.15) !important;
    }

    /* === Expander === */
    .streamlit-expanderHeader {
        background-color: white !important;
        border: 0.5px solid #e8dfd1 !important;
        border-radius: 10px !important;
        color: #3d2f24 !important;
    }

    /* === רדיו וצ'קבוקס === */
    .stRadio label, .stCheckbox label {
        color: #3d2f24 !important;
    }

    /* === ביישור גובה כרטיסי דשבורד === */
    [data-testid="column"] .stButton > button,
    [data-testid="stColumn"] .stButton > button {
        min-height: 78px !important;
        white-space: normal !important;
        line-height: 1.3 !important;
        padding: 10px 14px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    [data-testid="column"] h4,
    [data-testid="stColumn"] h4 {
        min-height: 60px !important;
        margin-bottom: 8px !important;
        display: flex !important;
        align-items: flex-end !important;
    }

    /* === הסתרת פוטר === */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Storage + state management
# ============================================================
@st.cache_resource
def get_storage():
    try:
        return GitHubStorage(
            token=st.secrets["github"]["token"],
            repo_name=st.secrets["github"]["repo"],
            file_path=st.secrets["github"].get("file_path", "data/tasks.json"),
            branch=st.secrets["github"].get("branch", "main"),
        )
    except KeyError:
        st.error("⚠️ חסרים פרטי גישה ל-GitHub. עיין ב-README להגדרת secrets.toml")
        st.stop()


def load_tasks():
    if "tasks" not in st.session_state:
        with st.spinner("טוען משימות מ-GitHub..."):
            st.session_state.tasks = get_storage().load()
    return st.session_state.tasks


def save_tasks(commit_message: str = "Update tasks"):
    try:
        get_storage().save(st.session_state.tasks, commit_message)
    except Exception as e:
        st.error(f"שגיאה בשמירה ל-GitHub: {e}")


def add_task_action(**kwargs):
    task = new_task(**kwargs)
    st.session_state.tasks.append(task)
    save_tasks(f"Add task: {task['title']}")


def update_task_action(task_id, **changes):
    for i, t in enumerate(st.session_state.tasks):
        if t["id"] == task_id:
            st.session_state.tasks[i] = update_task(t, **changes)
            save_tasks(f"Update: {t['title']}")
            return


def complete_task_action(task_id):
    for i, t in enumerate(st.session_state.tasks):
        if t["id"] == task_id:
            st.session_state.tasks[i] = complete_and_archive(t)
            save_tasks(f"Complete: {t['title']}")
            return


def restore_task_action(task_id):
    for i, t in enumerate(st.session_state.tasks):
        if t["id"] == task_id:
            st.session_state.tasks[i] = restore_from_archive(t)
            save_tasks(f"Restore: {t['title']}")
            return


def delete_task_action(task_id):
    title = next((t["title"] for t in st.session_state.tasks if t["id"] == task_id), "")
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    save_tasks(f"Delete: {title}")


def get_tasks(category=None, owner=None, archived=False):
    tasks = [t for t in st.session_state.tasks if t.get("archived", False) == archived]
    if category:
        tasks = [t for t in tasks if t.get("category") == category]
    if owner:
        tasks = [t for t in tasks if t.get("owner") == owner]
    return sorted(tasks, key=sort_key)


def navigate_to(page_id):
    """ניווט תכנותי בין עמודים - לשימוש עם on_click של כפתורים."""
    st.session_state.page_key = page_id


# ============================================================
# יומן שיחות - אחסון ופעולות
# ============================================================
@st.cache_resource
def get_calls_storage():
    try:
        return GitHubStorage(
            token=st.secrets["github"]["token"],
            repo_name=st.secrets["github"]["repo"],
            file_path="data/calls.json",
            branch=st.secrets["github"].get("branch", "main"),
        )
    except KeyError:
        st.error("⚠️ חסרים פרטי גישה ל-GitHub")
        st.stop()


def load_calls():
    if "calls" not in st.session_state:
        with st.spinner("טוען יומן שיחות..."):
            st.session_state.calls = get_calls_storage().load()
    return st.session_state.calls


def save_calls(commit_message: str = "Update calls"):
    try:
        get_calls_storage().save(st.session_state.calls, commit_message)
    except Exception as e:
        st.error(f"שגיאה בשמירת יומן שיחות: {e}")


def add_call_action(**kwargs):
    call = new_call(**kwargs)
    st.session_state.calls.append(call)
    save_calls(f"Log call with {call['contact_name']}")


def delete_call_action(call_id):
    name = next((c["contact_name"] for c in st.session_state.calls if c["id"] == call_id), "")
    st.session_state.calls = [c for c in st.session_state.calls if c["id"] != call_id]
    save_calls(f"Delete call log: {name}")


def get_calls(category=None):
    calls = list(st.session_state.calls)
    if category:
        calls = [c for c in calls if c.get("category") == category]
    return sorted(calls, key=lambda c: (c.get("date") or "", c.get("created_at") or ""), reverse=True)


# ============================================================
# רכיבי UI
# ============================================================
def render_due_badge(task):
    """מחזיר HTML של תג תאריך יעד עם צבע מתאים."""
    days = days_until_due(task)
    if days is None:
        return '<span class="due-badge-ok">ללא תאריך</span>'
    if days < 0:
        return f'<span class="due-badge-overdue">🔴 באיחור {-days} ימים</span>'
    if days <= DUE_SOON_DAYS:
        if days == 0:
            return '<span class="due-badge-soon">⚠️ היום!</span>'
        return f'<span class="due-badge-soon">⚠️ עוד {days} ימים</span>'
    return f'<span class="due-badge-ok">📅 {task["due_date"]}</span>'


def render_task_row(task, show_complete=True, show_restore=False, context_key=""):
    """שורת משימה אחת - צ'קבוקס, כותרת, badges, כפתורי עריכה/מחיקה.
    
    context_key מאפשר רינדור של אותה משימה במספר מקומות בלי התנגשות widget keys.
    """
    css_class = "task-card"
    if is_overdue(task):
        css_class += " overdue"
    elif is_due_soon(task):
        css_class += " due-soon"
    else:
        css_class += f" priority-{task['priority']}"

    cols = st.columns([0.06, 0.54, 0.18, 0.11, 0.11])
    k = f"{context_key}_{task['id']}"

    # צ'קבוקס להשלמה
    with cols[0]:
        if show_complete:
            if st.checkbox("✓", key=f"done_{k}", label_visibility="collapsed"):
                complete_task_action(task["id"])
                st.toast(f"✅ '{task['title']}' עבר לארכיון", icon="🗄️")
                st.rerun()
        elif show_restore:
            if st.button("↩️", key=f"restore_{k}", help="החזר ממשימות"):
                restore_task_action(task["id"])
                st.rerun()

    # תוכן המשימה
    with cols[1]:
        priority_icon = PRIORITY_ICONS[task["priority"]]
        cat_part = f'{CATEGORY_ICONS[task["category"]]} {CATEGORY_LABELS[task["category"]]}'
        owner_part = " · 👤 ריקי" if task.get("owner") == "riki" else ""
        prio_part = f' · דחיפות: {PRIORITY_LABELS[task["priority"]]}'
        meta_text = cat_part + owner_part + prio_part

        desc_html = ""
        if task.get("description"):
            desc_html = f'<div class="task-meta">📝 {task["description"]}</div>'

        card_html = (
            f'<div class="{css_class}" style="margin:0;">'
            f'<div class="task-title">{priority_icon} {task["title"]}</div>'
            f'<div class="task-meta">{meta_text}</div>'
            f'{desc_html}'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    # תאריך יעד
    with cols[2]:
        st.markdown(render_due_badge(task), unsafe_allow_html=True)

    # ערוך
    with cols[3]:
        if st.button("✏️", key=f"edit_{k}", help="ערוך"):
            st.session_state[f"editing_{task['id']}"] = True

    # מחק
    with cols[4]:
        if st.button("🗑️", key=f"del_{k}", help="מחק"):
            delete_task_action(task["id"])
            st.rerun()

    # טופס עריכה (נפתח כשלוחצים על ✏️)
    if st.session_state.get(f"editing_{task['id']}"):
        with st.expander("עריכת משימה", expanded=True):
            render_edit_form(task)


def render_edit_form(task):
    """טופס עריכה למשימה קיימת."""
    with st.form(f"edit_form_{task['id']}"):
        title = st.text_input("כותרת", value=task["title"])
        description = st.text_area("תיאור", value=task.get("description", ""), height=80)
        c1, c2, c3 = st.columns(3)
        with c1:
            priority = st.selectbox(
                "דחיפות",
                PRIORITIES,
                index=PRIORITIES.index(task["priority"]),
                format_func=lambda p: f"{PRIORITY_ICONS[p]} {PRIORITY_LABELS[p]}",
            )
        with c2:
            current_due = date.fromisoformat(task["due_date"]) if task.get("due_date") else None
            due_date = st.date_input("תאריך יעד", value=current_due, format="DD/MM/YYYY")
        with c3:
            if task["category"] == "moked":
                owner = st.selectbox(
                    "בעלים",
                    OWNERS,
                    index=OWNERS.index(task.get("owner", "self")),
                    format_func=lambda o: OWNER_LABELS[o],
                )
            else:
                owner = task.get("owner", "self")

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.form_submit_button("💾 שמור", use_container_width=True):
                update_task_action(
                    task["id"],
                    title=title,
                    description=description,
                    priority=priority,
                    due_date=due_date,
                    owner=owner,
                )
                del st.session_state[f"editing_{task['id']}"]
                st.rerun()
        with col_cancel:
            if st.form_submit_button("ביטול", use_container_width=True):
                del st.session_state[f"editing_{task['id']}"]
                st.rerun()


def render_add_form(category, default_owner="self", show_owner=False, key_suffix=""):
    """טופס הוספת משימה חדשה."""
    with st.expander("➕ הוספת משימה חדשה", expanded=False):
        with st.form(f"add_form_{category}_{key_suffix}", clear_on_submit=True):
            title = st.text_input("כותרת המשימה *", placeholder="למשל: לסיים הכנת דוח חודשי")
            description = st.text_area("תיאור (אופציונלי)", height=70)
            c1, c2 = st.columns(2)
            with c1:
                priority = st.selectbox(
                    "רמת דחיפות",
                    PRIORITIES,
                    index=1,  # default: medium
                    format_func=lambda p: f"{PRIORITY_ICONS[p]} {PRIORITY_LABELS[p]}",
                )
            with c2:
                due_date = st.date_input("תאריך יעד", value=None, format="DD/MM/YYYY")

            owner = default_owner
            if show_owner:
                owner = st.radio(
                    "משימה של:",
                    OWNERS,
                    format_func=lambda o: OWNER_LABELS[o],
                    horizontal=True,
                    index=OWNERS.index(default_owner),
                )

            if st.form_submit_button("הוסף משימה", type="primary", use_container_width=True):
                if not title.strip():
                    st.error("חובה להזין כותרת למשימה")
                else:
                    add_task_action(
                        title=title,
                        category=category,
                        priority=priority,
                        due_date=due_date,
                        owner=owner,
                        description=description,
                    )
                    st.toast(f"✅ המשימה נוספה", icon="✅")
                    st.rerun()


def render_task_list(tasks, empty_message="אין משימות", context_key=""):
    """רינדור רשימת משימות עם הודעה אם ריק."""
    if not tasks:
        st.info(empty_message)
        return
    for task in tasks:
        render_task_row(task, context_key=context_key)


# ============================================================
# רכיבי UI - יומן שיחות
# ============================================================
def render_add_call_form(category, key_suffix=""):
    """טופס תיעוד שיחה חדשה."""
    with st.expander("➕ תיעוד שיחה חדשה", expanded=False):
        with st.form(f"add_call_{category}_{key_suffix}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                contact_name = st.text_input("עם מי דיברת *", placeholder="שם איש הקשר")
            with c2:
                call_date = st.date_input("תאריך השיחה *", value=date.today(), format="DD/MM/YYYY")

            topic = st.text_input("נושא השיחה *", placeholder="במשפט אחד - על מה דיברנו")
            notes = st.text_area("פירוט נוסף (אופציונלי)", height=100, placeholder="סיכום מפורט, החלטות, מטלות שעלו...")

            if st.form_submit_button("💾 שמור שיחה", type="primary", use_container_width=True):
                if not contact_name.strip() or not topic.strip():
                    st.error("חובה למלא שם איש קשר ונושא השיחה")
                else:
                    add_call_action(
                        category=category,
                        contact_name=contact_name,
                        call_date=call_date,
                        topic=topic,
                        notes=notes,
                    )
                    st.toast("✅ השיחה תועדה", icon="📞")
                    st.rerun()


def render_call_log(category):
    """תצוגת יומן השיחות לקטגוריה - טופס הוספה + רשימת שיחות."""
    render_add_call_form(category)

    calls = get_calls(category=category)
    if not calls:
        st.info("אין שיחות מתועדות עדיין בקטגוריה זו")
        return

    st.markdown(f"**{len(calls)} שיחות מתועדות**")

    for call in calls:
        cols = st.columns([0.7, 0.2, 0.1])
        with cols[0]:
            contact = call.get("contact_name", "")
            topic = call.get("topic", "")
            notes_html = ""
            if call.get("notes"):
                notes_html = f'<div class="task-meta">📝 {call["notes"]}</div>'
            card_html = (
                f'<div class="call-card" style="margin:0;">'
                f'<div class="task-title">📞 {contact}</div>'
                f'<div class="task-meta">{topic}</div>'
                f'{notes_html}'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
        with cols[1]:
            st.markdown(
                f'<span class="due-badge-ok">📅 {call.get("date", "")}</span>',
                unsafe_allow_html=True,
            )
        with cols[2]:
            if st.button("🗑️", key=f"del_call_{call['id']}", help="מחק שיחה"):
                delete_call_action(call["id"])
                st.rerun()


# ============================================================
# סרגל צד + ניווט
# ============================================================
load_tasks()
load_calls()

st.sidebar.markdown("# 📋 ניהול משימות")
st.sidebar.markdown("---")

PAGES = {
    "dashboard": "📊 דשבורד",
    "crm": f"💼 {CATEGORY_LABELS['crm']}",
    "council_site": f"🌐 {CATEGORY_LABELS['council_site']}",
    "service_processes": f"🔄 {CATEGORY_LABELS['service_processes']}",
    "moked": f"📞 {CATEGORY_LABELS['moked']}",
    "routine": f"📋 {CATEGORY_LABELS['routine']}",
    "smart_add": "🤖 הוספה חכמה",
    "archive": "🗄️ ארכיון",
    "settings": "⚙️ הגדרות וסנכרון",
}
# אתחול state לניווט תכנותי בין עמודים
if "page_key" not in st.session_state:
    st.session_state.page_key = "dashboard"

page = st.sidebar.radio(
    "ניווט",
    options=list(PAGES.keys()),
    format_func=lambda k: PAGES[k],
    key="page_key",
    label_visibility="collapsed",
)

# התראות בסרגל הצד
st.sidebar.markdown("---")
active_tasks = [t for t in st.session_state.tasks if not t.get("archived")]
overdue = [t for t in active_tasks if is_overdue(t)]
due_soon = [t for t in active_tasks if is_due_soon(t)]

if overdue:
    st.sidebar.error(f"🔴 **{len(overdue)} משימות באיחור**")
if due_soon:
    st.sidebar.warning(f"🟡 **{len(due_soon)} משימות לסיום בקרוב**")
if not overdue and not due_soon:
    st.sidebar.success("✅ הכל בשליטה")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 רענן מ-GitHub", use_container_width=True):
    if "tasks" in st.session_state:
        del st.session_state.tasks
    st.rerun()


# ============================================================
# 📊 דשבורד
# ============================================================
def page_dashboard():
    st.markdown(
        '<div style="text-align:center; padding:28px 0 18px; margin-bottom:24px; border-bottom:1px solid #e8dfd1;">'
        '<h1 style="color:#3d2f24; font-size:2.4em; font-weight:600; margin:0; letter-spacing:-0.02em;">'
        '📋 ניהול משימות מחלקת שירות'
        '</h1>'
        '<p style="color:#8a7a6c; font-size:0.95em; margin:10px 0 0 0;">דשבורד מרכזי</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # === קטגוריות בראש הדף - לחיצה מנווטת לעמוד הפרויקט ===
    st.caption("💡 לחיצה על כפתור מובילה ישירות לעמוד הפרויקט")
    cat_cols = st.columns(len(CATEGORIES))
    for col, cat in zip(cat_cols, CATEGORIES):
        with col:
            cat_tasks = [t for t in active_tasks if t.get("category") == cat]
            cat_overdue = [t for t in cat_tasks if is_overdue(t)]
            cat_soon = [t for t in cat_tasks if is_due_soon(t)]

            st.markdown(f"#### {CATEGORY_ICONS[cat]} {CATEGORY_LABELS[cat]}")

            st.button(
                f"📋 {len(cat_tasks)} משימות פעילות",
                key=f"dash_nav_{cat}",
                use_container_width=True,
                on_click=navigate_to,
                args=(cat,),
                type="primary" if cat_overdue else "secondary",
            )

            # באדג'ים מתחת לכפתור - בגובה קבוע לאחידות
            badge_parts = []
            if cat_overdue:
                badge_parts.append(f"🔴 {len(cat_overdue)} באיחור")
            if cat_soon:
                badge_parts.append(f"🟡 {len(cat_soon)} בקרוב")
            badges_text = " · ".join(badge_parts) if badge_parts else "&nbsp;"
            st.markdown(
                f'<div style="text-align:center;font-size:0.85em;color:#8a7a6c;height:24px;padding-top:6px;overflow:hidden;">{badges_text}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # === התראות בולטות ===
    if overdue:
        st.error(f"### 🔴 {len(overdue)} משימות באיחור — דרושה תשומת לב מיידית")
    if due_soon:
        st.warning(f"### 🟡 {len(due_soon)} משימות עם דד-ליין ביומיים הקרובים")

    # === מטריקות ===
    total = len(active_tasks)
    completed = len([t for t in st.session_state.tasks if t.get("archived")])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button(
            f"📋 {total} משימות פעילות",
            key="metric_active",
            use_container_width=True,
            on_click=navigate_to,
            args=("all_active",),
        )
    with c2:
        st.button(
            f"✅ {completed} הושלמו",
            key="metric_completed",
            use_container_width=True,
            on_click=navigate_to,
            args=("archive",),
        )
    with c3:
        st.button(
            f"🔴 {len(overdue)} באיחור",
            key="metric_overdue",
            use_container_width=True,
            on_click=navigate_to,
            args=("overdue_view",),
            type="primary" if overdue else "secondary",
        )
    with c4:
        st.button(
            f"🟡 {len(due_soon)} בקרוב (יומיים)",
            key="metric_soon",
            use_container_width=True,
            on_click=navigate_to,
            args=("due_soon_view",),
        )

    st.markdown("---")

    # === משימות באיחור + בקרוב ===
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 משימות באיחור")
        render_task_list(overdue, empty_message="אין משימות באיחור 🎉", context_key="overdue")
    with col2:
        st.subheader("🟡 לסיום ביומיים הקרובים")
        render_task_list(due_soon, empty_message="אין משימות לסיום בקרוב", context_key="soon")

    st.markdown("---")

    # === פתוחות לפי דחיפות ===
    st.subheader("📋 משימות פתוחות לפי דחיפות")
    for prio in ["urgent", "high", "medium", "low"]:
        prio_tasks = [t for t in active_tasks if t.get("priority") == prio]
        if prio_tasks:
            with st.expander(
                f"{PRIORITY_ICONS[prio]} דחיפות {PRIORITY_LABELS[prio]} ({len(prio_tasks)})",
                expanded=(prio in ["urgent", "high"]),
            ):
                render_task_list(prio_tasks, context_key=f"prio_{prio}")


# ============================================================
# עמודי קטגוריה
# ============================================================
def page_category(cat_key, show_riki=False):
    icon = CATEGORY_ICONS[cat_key]
    label = CATEGORY_LABELS[cat_key]
    st.title(f"{icon} {label}")

    if show_riki:
        # מוקד 106: שלוש לשוניות - שלי / ריקי / יומן שיחות
        tab_mine, tab_riki, tab_calls = st.tabs([
            "👤 המשימות שלי",
            "👥 המשימות של ריקי",
            "📞 יומן שיחות",
        ])

        with tab_mine:
            my_tasks = get_tasks(category=cat_key, owner="self")
            render_add_form(cat_key, default_owner="self", show_owner=False, key_suffix="self")
            st.markdown(f"**{len(my_tasks)} משימות פעילות**")
            render_task_list(my_tasks, empty_message="אין משימות פעילות שלך כאן", context_key=f"{cat_key}_self")

        with tab_riki:
            riki_tasks = get_tasks(category=cat_key, owner="riki")
            render_add_form(cat_key, default_owner="riki", show_owner=False, key_suffix="riki")
            st.markdown(f"**{len(riki_tasks)} משימות פעילות**")
            render_task_list(riki_tasks, empty_message="אין משימות פעילות של ריקי", context_key=f"{cat_key}_riki")

        with tab_calls:
            render_call_log(cat_key)
    else:
        # שאר הפרויקטים: שתי לשוניות - משימות / יומן שיחות
        tab_tasks, tab_calls = st.tabs(["📋 משימות", "📞 יומן שיחות"])

        with tab_tasks:
            tasks = get_tasks(category=cat_key)
            render_add_form(cat_key, default_owner="self", show_owner=False)
            st.markdown(f"**{len(tasks)} משימות פעילות**")
            render_task_list(tasks, empty_message="אין משימות פעילות בקטגוריה זו", context_key=cat_key)

        with tab_calls:
            render_call_log(cat_key)


# ============================================================
# 🤖 הוספה חכמה (Claude AI)
# ============================================================
def page_smart_add():
    st.title("🤖 הוספה חכמה עם Claude")
    st.markdown(
        "הדביקי כאן **טקסט חופשי** - אימייל, הודעה, סיכום פגישה, כל דבר. "
        "Claude יקרא, יסווג לקטגוריה, יחלץ דד-ליין ודחיפות, ויציע משימה לאישור שלך."
    )

    # בדיקת מפתח API
    try:
        api_key = st.secrets["anthropic"]["api_key"]
    except (KeyError, FileNotFoundError):
        st.warning(
            "⚠️ לא הוגדר Anthropic API key. כדי להפעיל את הסיווג החכם:\n"
            "1. הירשמי ב-https://console.anthropic.com\n"
            "2. צרי API key\n"
            "3. הוסיפי ב-`.streamlit/secrets.toml`:\n"
            "```toml\n[anthropic]\napi_key = \"sk-ant-...\"\n```"
        )
        return

    # תיבת הקלט
    text = st.text_area(
        "טקסט לסיווג",
        height=200,
        placeholder="דוגמה: 'בוקר טוב, צריך לבדוק תקלה באתר המועצה שלא מציג נכון את לוח האירועים. עד יום חמישי לכל המאוחר.'",
        key="smart_add_text",
    )

    col_btn, col_clear = st.columns([0.3, 0.7])
    with col_btn:
        analyze_clicked = st.button(
            "🪄 נתח עם Claude",
            type="primary",
            disabled=(not text.strip()),
            use_container_width=True,
        )
    with col_clear:
        if "ai_suggestion" in st.session_state and st.button("נקה תוצאה"):
            del st.session_state.ai_suggestion
            st.rerun()

    if analyze_clicked:
        with st.spinner("Claude קורא ומחליט..."):
            try:
                suggestion = classify_text(text, api_key)
                st.session_state.ai_suggestion = suggestion
                st.session_state.ai_source_text = text
            except Exception as e:
                st.error(f"שגיאה בסיווג: {e}")
                return

    # הצגת הצעת Claude לאישור
    if "ai_suggestion" in st.session_state:
        sug = st.session_state.ai_suggestion
        st.markdown("---")
        st.subheader("📋 הצעת Claude")

        # ציון ביטחון
        confidence = sug.get("confidence", 0.0)
        if confidence >= 0.8:
            st.success(f"רמת ביטחון: {int(confidence*100)}% ✅")
        elif confidence >= 0.5:
            st.warning(f"רמת ביטחון: {int(confidence*100)}% ⚠️ - מומלץ לבדוק לפני אישור")
        else:
            st.error(f"רמת ביטחון: {int(confidence*100)}% ❌ - הסיווג לא ברור, אנא ערכי ידנית")

        if sug.get("reasoning"):
            st.caption(f"💭 {sug['reasoning']}")

        # טופס אישור/עריכה
        with st.form("confirm_ai_suggestion"):
            title = st.text_input("כותרת", value=sug.get("suggested_title", ""))

            c1, c2 = st.columns(2)
            with c1:
                category = st.selectbox(
                    "קטגוריה",
                    CATEGORIES,
                    index=CATEGORIES.index(sug["category"]),
                    format_func=lambda c: f"{CATEGORY_ICONS[c]} {CATEGORY_LABELS[c]}",
                )
            with c2:
                priority = st.selectbox(
                    "דחיפות",
                    PRIORITIES,
                    index=PRIORITIES.index(sug["priority"]),
                    format_func=lambda p: f"{PRIORITY_ICONS[p]} {PRIORITY_LABELS[p]}",
                )

            c3, c4 = st.columns(2)
            with c3:
                suggested_due = None
                if sug.get("due_date"):
                    try:
                        suggested_due = date.fromisoformat(sug["due_date"])
                    except (ValueError, TypeError):
                        pass
                due_date = st.date_input("תאריך יעד", value=suggested_due, format="DD/MM/YYYY")
            with c4:
                # בעלים רק אם הקטגוריה היא מוקד
                if category == "moked":
                    owner = st.radio(
                        "משימה של:",
                        OWNERS,
                        index=OWNERS.index(sug.get("owner", "self")),
                        format_func=lambda o: OWNER_LABELS[o],
                        horizontal=True,
                    )
                else:
                    owner = "self"
                    st.caption("(תכונת ריקי רלוונטית רק במוקד)")

            description = st.text_area(
                "תיאור (טקסט המקור)",
                value=st.session_state.get("ai_source_text", ""),
                height=100,
            )

            col_create, col_cancel = st.columns(2)
            with col_create:
                if st.form_submit_button("✅ צור משימה", type="primary", use_container_width=True):
                    if not title.strip():
                        st.error("חובה להזין כותרת")
                    else:
                        add_task_action(
                            title=title,
                            category=category,
                            priority=priority,
                            due_date=due_date,
                            owner=owner,
                            description=description,
                            source="ai_classified",
                        )
                        del st.session_state.ai_suggestion
                        if "ai_source_text" in st.session_state:
                            del st.session_state.ai_source_text
                        st.success("המשימה נוספה! 🎉")
                        st.rerun()
            with col_cancel:
                if st.form_submit_button("ביטול", use_container_width=True):
                    del st.session_state.ai_suggestion
                    st.rerun()

# ============================================================
# רשימות מסוננות (נכנסים מהדשבורד דרך הקוביות)
# ============================================================
def page_all_active():
    st.title("📋 כל המשימות הפעילות")
    tasks = sorted(
        [t for t in st.session_state.tasks if not t.get("archived")],
        key=sort_key,
    )
    if not tasks:
        st.info("אין משימות פעילות")
        return
    st.markdown(f"**{len(tasks)} משימות**")
    render_task_list(tasks, context_key="all_active")


def page_overdue_view():
    st.title("🔴 משימות באיחור")
    tasks = sorted(
        [t for t in st.session_state.tasks if not t.get("archived") and is_overdue(t)],
        key=sort_key,
    )
    if not tasks:
        st.success("🎉 אין משימות באיחור")
        return
    st.markdown(f"**{len(tasks)} משימות באיחור**")
    render_task_list(tasks, context_key="overdue_view")


def page_due_soon_view():
    st.title("🟡 משימות לסיום בקרוב")
    tasks = sorted(
        [t for t in st.session_state.tasks if not t.get("archived") and is_due_soon(t)],
        key=sort_key,
    )
    if not tasks:
        st.info("אין משימות לסיום בקרוב")
        return
    st.markdown(f"**{len(tasks)} משימות**")
    render_task_list(tasks, context_key="due_soon_view")
# ============================================================
# 🗄️ ארכיון
# ============================================================
def page_archive():
    st.title("🗄️ ארכיון")
    archived = [t for t in st.session_state.tasks if t.get("archived")]

    if not archived:
        st.info("הארכיון ריק. משימות שתסמני כהושלמו יופיעו כאן.")
        return

    # פילטרים
    c1, c2 = st.columns([0.3, 0.7])
    with c1:
        cat_filter = st.selectbox(
            "סינון לפי קטגוריה",
            ["all"] + CATEGORIES,
            format_func=lambda x: "כל הקטגוריות" if x == "all" else f"{CATEGORY_ICONS[x]} {CATEGORY_LABELS[x]}",
        )
    with c2:
        search = st.text_input("חיפוש בכותרת", placeholder="הקלידי טקסט לחיפוש...")

    filtered = archived
    if cat_filter != "all":
        filtered = [t for t in filtered if t.get("category") == cat_filter]
    if search:
        filtered = [t for t in filtered if search.lower() in t.get("title", "").lower()]

    # מיון: האחרונות שהושלמו ראשונות
    filtered = sorted(filtered, key=lambda t: t.get("completed_at") or "", reverse=True)

    st.markdown(f"**{len(filtered)} משימות בארכיון**")
    for task in filtered:
        completed_date = (task.get("completed_at") or "")[:10]
        with st.container():
            cols = st.columns([0.06, 0.6, 0.2, 0.07, 0.07])
            with cols[0]:
                if st.button("↩️", key=f"restore_{task['id']}", help="החזר ממשימות"):
                    restore_task_action(task["id"])
                    st.rerun()
            with cols[1]:
                cat_part = f'{CATEGORY_ICONS[task["category"]]} {CATEGORY_LABELS[task["category"]]}'
                owner_part = " · 👤 ריקי" if task.get("owner") == "riki" else ""
                prio_part = f' · דחיפות: {PRIORITY_LABELS[task["priority"]]}'
                meta_text = cat_part + owner_part + prio_part
                card_html = (
                    f'<div class="task-card" style="margin:0;opacity:0.85;">'
                    f'<div class="task-title">✅ {task["title"]}</div>'
                    f'<div class="task-meta">{meta_text}</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f'<span class="due-badge-ok">הושלמה: {completed_date}</span>', unsafe_allow_html=True)
            with cols[3]:
                pass
            with cols[4]:
                if st.button("🗑️", key=f"del_arch_{task['id']}", help="מחק לצמיתות"):
                    delete_task_action(task["id"])
                    st.rerun()


# ============================================================
# ⚙️ הגדרות וסנכרון אאוטלוק
# ============================================================
def page_settings():
    st.title("⚙️ הגדרות וסנכרון")

    # סטטוס מפתח Anthropic
    st.subheader("🤖 Anthropic API (להוספה חכמה)")
    try:
        _ = st.secrets["anthropic"]["api_key"]
        st.success("✅ מפתח Anthropic מוגדר - הוספה חכמה פעילה")
    except (KeyError, FileNotFoundError):
        st.error("❌ מפתח Anthropic לא מוגדר. עיין ב-README.")

    st.markdown("---")

    # סטטוס Outlook
    st.subheader("🔗 סנכרון Outlook")
    try:
        outlook_configured = bool(st.secrets["outlook"].get("client_id"))
    except (KeyError, FileNotFoundError):
        outlook_configured = False

    if outlook_configured:
        st.success("✅ פרטי Azure מוגדרים - סנכרון Outlook מוכן")
        st.info("💡 חיבור חי ל-Outlook יתווסף בעדכון הבא של המערכת.")
    else:
        st.warning("⏳ סנכרון Outlook עוד לא הוגדר")

        st.markdown("**צ'קליסט להפעלת סנכרון Outlook:**")
        st.markdown("""
        - [ ] שליחת מייל ל-IT של המועצה (יש מייל מוכן בהודעה הקודמת)
        - [ ] קבלת 3 הפרטים מ-IT:
          - Application (client) ID
          - Directory (tenant) ID
          - Client Secret
        - [ ] הוספת הפרטים ל-`.streamlit/secrets.toml`:
          ```toml
          [outlook]
          tenant_id = "..."
          client_id = "..."
          client_secret = "..."
          ```
        - [ ] לחזור אליי כדי שאוסיף את שכבת הסנכרון
        """)

        with st.expander("📖 מה IT צריך לעשות בצד שלהם"):
            st.markdown("""
            1. כניסה ל-[Azure Portal](https://portal.azure.com) → **Azure Active Directory** → **App registrations**
            2. **New registration**:
               - Name: Personal Task Manager
               - Supported account types: Single tenant
               - Redirect URI: ללא (Device Code Flow)
            3. תחת **API permissions** (delegated):
               - Microsoft Graph → `Tasks.Read`
               - Microsoft Graph → `Mail.Read`
               - Microsoft Graph → `offline_access`
            4. **Grant admin consent** עבור ההרשאות
            5. תחת **Certificates & secrets** → **New client secret**
            6. שליחה אלייך של 3 הערכים (Client ID, Tenant ID, Secret value)
            """)

    st.markdown("---")
    st.subheader("📊 מצב מערכת")
    c1, c2, c3 = st.columns(3)
    c1.metric("סה״כ משימות במערכת", len(st.session_state.tasks))
    c2.metric("פעילות", len([t for t in st.session_state.tasks if not t.get("archived")]))
    c3.metric("בארכיון", len([t for t in st.session_state.tasks if t.get("archived")]))

    st.markdown("---")
    st.subheader("⚠️ אזור מסוכן")
    with st.expander("מחיקת כל המשימות"):
        st.warning("פעולה זו לא הפיכה. המידע יימחק מקובץ ה-JSON ב-GitHub.")
        confirm = st.text_input("הקלידי 'מחק הכל' לאישור")
        if st.button("🗑️ מחק את כל המשימות", disabled=(confirm != "מחק הכל")):
            st.session_state.tasks = []
            save_tasks("Wipe all tasks")
            st.success("כל המשימות נמחקו")
            st.rerun()


# ============================================================
# Router
# ============================================================
if page == "dashboard":
    page_dashboard()
elif page == "moked":
    page_category("moked", show_riki=True)
elif page == "council_site":
    page_category("council_site")
elif page == "crm":
    page_category("crm")
elif page == "service_processes":
    page_category("service_processes")
elif page == "routine":
    page_category("routine")
elif page == "smart_add":
    page_smart_add()
elif page == "all_active":
    page_all_active()
elif page == "overdue_view":
    page_overdue_view()
elif page == "due_soon_view":
    page_due_soon_view()
elif page == "archive":
    page_archive()
elif page == "settings":
    page_settings()
