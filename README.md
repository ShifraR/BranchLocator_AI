# 🏙️ BranchLocator AI - מאתר סניפים חכם

מערכת מבוססת AI לאיתור, חילוץ וריכוז רשימות סניפים של חברות בישראל מרחבי הרשת.
המערכת משתמשת ב-LLM (Gemini) כדי לייצר שאילתות חיפוש חכמות ולחלץ נתונים מובנים מתוך תוצאות חיפוש גולמיות.


## 🛠️ התקנה והרצה

### 1. דרישות קדם
- Python 3.10 ומעלה.
- מפתח API עבור [Google AI Studio](https://aistudio.google.com/).
- מפתח API עבור [Serper.dev](https://serper.dev/).

### 2. הגדרת הסביבה
יש לשכפל את הפרויקט וליצור סביבה וירטואלית:
```bash
# יצירת סביבה וירטואלית
python -m venv venv

# הפעלה (Windows)
venv\Scripts\activate
```

### 3. התקנת הספריות הדרושות
```bash
pip install -r requirements.txt
```

### 4. הגדרת מפתחות
יש להוסיף את המפתחות לקובץ .env

### 5. הרצת האפליקציה
```bash
streamlit run web_app.py
```

