import streamlit as st
import pandas as pd
import os
import requests
import json
from dotenv import load_dotenv

# הגדרות נטפרי
netfree_windows_path = r'C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt'
if os.name == 'nt' and os.path.exists(netfree_windows_path):
    os.environ['SSL_CERT_FILE'] = netfree_windows_path
    os.environ['REQUESTS_CA_BUNDLE'] = netfree_windows_path

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def search_serper(company_name):
    """חיפוש יציב דרך Serper - ללא הגבלות 429 קשות"""
    url = "https://google.serper.dev/search"
    query = f"סניפים של {company_name} בישראל רשימה כתובות"
    payload = {"q": query, "gl": "il", "hl": "iw", "num": 15}
    headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get('organic', [])

def extract_with_gemini(raw_results, company_name):
    """חילוץ חכם של נתונים מתוך תוצאות החיפוש"""
    context = ""
    for res in raw_results:
        context += f"Source: {res.get('link')}\nInfo: {res.get('title')} - {res.get('snippet')}\n---\n"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    אתה מנתח נתונים מקצועי. חלץ רשימת סניפים של {company_name} מהטקסט הבא.
    הנחיות:
    1. החזר רשימת JSON בלבד של אובייקטים.
    2. כל אובייקט יכיל: 'שם הסניף', 'כתובת', 'עיר', 'מקור'.
    3. אם יש סניפים כפולים, אחד אותם לרשומה אחת.
    
    טקסט לניתוח:
    {context}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=60)
    result = response.json()
    
    try:
        raw_text = result['candidates'][0]['content']['parts'][0]['text']
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return []

# ממשק המשתמש
st.set_page_config(page_title="Branch Locator AI", layout="wide")
st.title("🏙️ מאתר סניפים חכם (Hybrid AI)")

company = st.text_input("הכניסי שם חברה (למשל: סופר-פארם, בנק דיסקונט):")

if st.button("חפש סניפים"):
    if company:
        with st.status("סורק נתונים...", expanded=True) as status:
            st.write("🌐 אוסף מידע מרשת האינטרנט...")
            results = search_serper(company)
            st.write("🧠 מנתח ומנקה כפילויות בעזרת AI...")
            branches = extract_with_gemini(results, company)
            status.update(label="הסריקה הושלמה!", state="complete")
        
        if branches:
            df = pd.DataFrame(branches)
            st.dataframe(df, use_container_width=True)
            st.download_button("הורדת CSV", df.to_csv(index=False).encode('utf-8-sig'), "branches.csv")
        else:
            st.error("לא נמצאו סניפים. נסי לחפש שם חברה אחר.")