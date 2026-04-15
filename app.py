import streamlit as st
import pandas as pd
from config import setup_environment
from logic import fetch_search_results, extract_branches_raw, filter_with_embeddings

# 1. טעינת הגדרות
keys = setup_environment()

st.set_page_config(page_title="Branch Locator - Separate Lists", layout="wide")

# עיצוב RTL
st.markdown("""
    <style>
    .main, .stApp { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏙️ מערכת איתור ואיחוד סניפים (PoC)")
st.write("הזינו רשימת חברות. המערכת תציג רשימה נפרדת ומסוננת לכל חברה.")

# 2. קלט רשימה
input_text = st.text_area("רשימת חברות (כל חברה בשורה חדשה):", placeholder="ארומה\nרמי לוי", height=150)

if st.button("הפעל סריקה מפוצלת"):
    if input_text:
        companies = [c.strip() for c in input_text.replace(',', '\n').split('\n') if c.strip()]
        
        # רשימה גלובלית רק לצורך הורדת קובץ אחד בסוף (אופציונלי)
        all_results_combined = []
        
        progress_bar = st.progress(0)
        
        for index, company in enumerate(companies):
            # יצירת "קופסה" (Expander) לכל חברה כדי שהמסך לא יהיה עמוס מדי
            with st.expander(f"📍 תוצאות עבור: {company}", expanded=True):
                
                with st.status(f"מנתח את {company}...", expanded=False) as status:
                    # שלב 1: איתור
                    st.write("🌐 מחפש בגוגל...")
                    raw_data = fetch_search_results(company, keys["SERPER_KEY"])
                    
                    # שלב 2: חילוץ
                    st.write("🧠 מחלץ נתונים...")
                    raw_branches = extract_branches_raw(raw_data, company, keys["GEMINI_KEY"])
                    
                    # שלב 3: איחוד (Embeddings)
                    st.write("📏 מסנן כפילויות וקטורי...")
                    unique_branches = filter_with_embeddings(raw_branches, keys["GEMINI_KEY"])
                    
                    status.update(label=f"הסריקה של {company} הושלמה!", state="complete")
                
                # הצגת הטבלה הספציפית לחברה זו
                if unique_branches:
                    df_company = pd.DataFrame(unique_branches)
                    st.dataframe(df_company, use_container_width=True)
                    
                    # כפתור הורדה ספציפי לחברה זו
                    csv_comp = df_company.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(f"הורדת רשימת {company} (CSV)", csv_comp, f"{company}_branches.csv", key=f"dl_{company}")
                    
                    # הוספה לרשימה הכללית (לגיבוי)
                    for b in unique_branches:
                        b['חברה מחפשת'] = company
                    all_results_combined.extend(unique_branches)
                else:
                    st.warning(f"לא נמצאו סניפים עבור {company}.")
            
            # עדכון פס התקדמות כללי
            progress_bar.progress((index + 1) / len(companies))

        # 3. בסוף הכל - כפתור אחד שמוריד את הכל ביחד (בונוס למבחן)
        if all_results_combined:
            st.divider()
            st.subheader("📊 סיכום סופי")
            full_df = pd.DataFrame(all_results_combined)
            final_csv = full_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 הורדת דוח מאוחד של כל החברות", final_csv, "all_companies_combined.csv", "text/csv")
            
    else:
        st.warning("נא להזין חברות.")