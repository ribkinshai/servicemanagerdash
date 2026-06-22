# 📋 מערכת ניהול משימות - מועצה

מערכת אישית לניהול משימות עבור 3 תחומי אחריות: **מוקד**, **אתר המועצה**, **מערכת CRM**.
נבנתה ב-Streamlit עם אחסון JSON ברפו של GitHub (כל שינוי = commit, היסטוריה מלאה).

## פיצ'רים

- 🏢 **3 קטגוריות** עם עמוד ייעודי לכל אחת
- 👥 **תת-טבלה לריקי** תחת קטגוריית מוקד
- 🔴 **התראת איחור** — משימות באיחור מוצגות באדום
- 🟡 **התראת דד-ליין מתקרב** — יומיים לפני, מוצגות בצהוב
- ⚡ **4 רמות דחיפות** — נמוכה / בינונית / גבוהה / דחוף
- ✅ **סימון V והעברה לארכיון** — המשימות נשמרות, לא נמחקות
- 📊 **דשבורד** — סטטיסטיקות, באיחור, בקרוב, פתוחות לפי דחיפות
- 🔄 **שמירה אוטומטית ל-GitHub** אחרי כל שינוי

## התקנה והרצה

### 1. הכנת הרפו ב-GitHub

צרי רפו חדש ב-GitHub שישמש כמסד נתונים (למשל `task-manager-data`).
מומלץ שיהיה **פרטי**. את הקובץ `data/tasks.json` המערכת תיצור לבד בשמירה הראשונה.

### 2. יצירת Personal Access Token

1. כניסה ל-https://github.com/settings/tokens
2. **Generate new token** → Classic
3. הרשאות נדרשות: `repo` (כל ההרשאות תחת זה)
4. שמרי את ה-token

### 3. הגדרת secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

ערכי את `.streamlit/secrets.toml`:
```toml
[github]
token = "ghp_..."           # ה-token שיצרת
repo = "your-name/task-manager-data"  # שם הרפו
```

### 4. התקנת dependencies והרצה

```bash
pip install -r requirements.txt
streamlit run app.py
```

## פריסה ל-Streamlit Community Cloud

1. דחפי את הקוד הזה (בלי `secrets.toml`!) לרפו GitHub.
2. כניסה ל-https://share.streamlit.io ופריסה מהרפו.
3. ב-**Settings → Secrets** של האפליקציה, הדביקי את תוכן `secrets.toml` שלך.
4. האפליקציה תהיה זמינה מכל מקום עם גישה דרך הדפדפן.

## מבנה הפרויקט

```
task-manager/
├── app.py                  # אפליקציית Streamlit ראשית
├── models.py               # מודל נתונים + לוגיקת תאריכים/דחיפויות
├── storage.py              # שכבת אחסון GitHub
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── secrets.toml.example
```

## שלב הבא: סנכרון Outlook

הסנכרון עם Outlook נמצא בעמוד **הגדרות וסנכרון** באפליקציה.
הוא דורש הגדרת אפליקציה ב-Azure AD (Microsoft Graph API).
הפרטים המלאים בעמוד ההגדרות באפליקציה.
