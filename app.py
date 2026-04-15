import streamlit as st
import pandas as pd
from config import setup_environment
from logic import fetch_search_results, extract_branches

# 1. טעינת הגדרות (מפתחות ונטפרי)
keys = setup_environment()

# 2. הגדרות דף ועיצוב RTL (יישור לימין)
st.set_page_config(page_title="Branch Locator", layout="wide")

st.markdown("""
    <style>
    /* הופך את כל האפליקציה לימין לשמאל */
    .main, .stApp { direction: rtl; text-align: right; }
    /* דואג שגם תיבות הטקסט והכפתורים יתיישרו */
    div[data-testid="stMarkdownContainer"] > p { text-align: right; }
    button { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏙️ מאתר סניפים חכם")
st.write("הכניסי שם חברה כדי להתחיל בסריקה חכמה של האינטרנט.")

company = st.text_input("שם החברה לחיפוש:", placeholder="לדוגמה: אופטיקה הלפרין")

if st.button("התחל חיפוש"):
    if company:
        # 3. שימוש ב-st.status כדי להראות את התהליך (בדיוק כמו שאהבת!)
        with st.status("מבצע מחקר שוק...", expanded=True) as status:
            
            st.write("🔍 מחפש מקורות מידע בגוגל...")
            raw_data = fetch_search_results(company, keys["SERPER_KEY"])
            
            st.write(f"🧠 מחלץ סניפים מ-{len(raw_data)} מקורות שמצאתי...")
            branches = extract_branches(raw_data, company, keys["GEMINI_KEY"])
            
            if branches:
                status.update(label="הסריקה הושלמה בהצלחה!", state="complete", expanded=False)
            else:
                status.update(label="הסריקה הסתיימה ללא תוצאות.", state="error", expanded=True)
            
        # 4. הצגת התוצאות
        if branches:
            st.subheader(f"נמצאו {len(branches)} סניפים עבור '{company}':")
            df = pd.DataFrame(branches)
            st.dataframe(df, use_container_width=True)
            
            # כפתור הורדה
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("הורדת הרשימה כ-CSV", csv, f"{company}_branches.csv", "text/csv")
    else:
        st.warning("בבקשה הכניסי שם חברה.")