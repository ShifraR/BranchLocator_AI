import streamlit as st
import pandas as pd
import os
import requests
import json
from dotenv import load_dotenv

# --- הגדרות נטפרי וסביבה ---
netfree_windows_path = r'C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt'
if os.name == 'nt' and os.path.exists(netfree_windows_path):
    os.environ['SSL_CERT_FILE'] = netfree_windows_path
    os.environ['REQUESTS_CA_BUNDLE'] = netfree_windows_path

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

# --- פונקציות הלוגיקה (מועתקות מ-main.py עם התאמות קלות) ---

def generate_queries(company_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    prompt = f"ייצר עבורי 4 שאילתות חיפוש בגוגל לאיתור רשימת סניפי {company_name} בישראל. החזר רק רשימה של שאילתות בשורות נפרדות."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status() # יזרוק שגיאה אם הסטטוס הוא לא 200
        result = response.json()
        
        # בדיקה אם גוגל החזיר 'candidates'
        if 'candidates' in result and result['candidates'][0].get('content'):
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            return [q.strip("- *") for q in text_response.strip().split('\n') if q.strip()]
        else:
            # אם אין 'candidates', נדפיס את התשובה המלאה כדי להבין למה
            st.error(f"גוגל לא החזיר תוצאות. תשובה גולמית: {result}")
            return []
            
    except Exception as e:
        st.error(f"שגיאה בפנייה לג'מיני: {e}")
        if hasattr(e, 'response') and e.response is not None:
            st.code(e.response.text) # מציג את פירוט השגיאה מהשרת
        return []

def search_serper(query):
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    payload = {"q": query, "gl": "il", "hl": "iw"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get('organic', [])

def extract_to_json(raw_results):
    context = ""
    for res in raw_results[:15]: # הגבלה ל-15 תוצאות ראשונות כדי לחסוך זמן/טוקנים ב-PoC
        context += f"Title: {res.get('title')}\nSnippet: {res.get('snippet')}\nLink: {res.get('link')}\n---\n"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    prompt = f"""
    חלץ רשימת סניפים בפורמט JSON מהטקסט הבא. 
    עבור כל סניף: 'שם הסניף', 'כתובת', 'מקור המידע'.
    החזר רשימת JSON בלבד!
    טקסט: {context}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=60)
    raw_json = response.json()['candidates'][0]['content']['parts'][0]['text']
    clean_json = raw_json.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# --- ממשק Streamlit ---

st.set_page_config(page_title="סורק סניפי AI", layout="wide")

# CSS ליישור לימין
st.markdown("""
    <style>
    .main, .stApp { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏙️ מאתר סניפים חכם (AI)")
st.write("הכניסי שם של חברה, והמערכת תסרוק את הרשת ותחלץ רשימת סניפים מסודרת.")

company_input = st.text_input("שם החברה לחיפוש:", placeholder="לדוגמה: ארומה, בנק הפועלים, שופרסל...")

if st.button("התחל סריקה"):
    if not company_input:
        st.warning("בבקשה הכניסי שם חברה.")
    else:
        with st.status("עובד על זה...", expanded=True) as status:
            # שלב 1
            st.write("🔍 מייצר שאילתות חיפוש...")
            queries = generate_queries(company_input)
            
            # שלב 2
            st.write("🌐 אוסף מידע מגוגל...")
            all_results = []
            for q in queries:
                all_results.extend(search_serper(q))
            
            # שלב 3
            st.write(f"🧠 מעבד {len(all_results)} מקורות ומחלץ נתונים...")
            branches = extract_to_json(all_results)
            
            status.update(label="הסריקה הושלמה!", state="complete", expanded=False)

        if branches:
            st.subheader(f"נמצאו {len(branches)} סניפים עבור '{company_input}'")
            
            # הצגת הנתונים בטבלה יפה
            df = pd.DataFrame(branches)
            st.dataframe(df, use_container_width=True)
            
            # אפשרות להורדת התוצאות ב-CSV
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("הורדת הרשימה כ-CSV", csv, "branches.csv", "text/csv")
        else:
            st.error("לא הצלחנו לחלץ סניפים. נסי שוב או שנו את השאילתה.")