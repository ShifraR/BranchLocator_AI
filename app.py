import streamlit as st
from logic import run_multi_company_researcher

st.set_page_config(page_title="AI Branch Investigator", page_icon="🕵️", layout="wide")

st.title("🕵️ סוכן חוקר: הצלבת מפות ואינטרנט")
st.markdown("הסוכן מבצע מחקר דו-שלבי: קודם ב-**Google Maps** ואז ב-**Google Search** לאימות והשלמת נתונים.")

# קלט המשתמש
input_text = st.text_area(
    "הכניסי שמות חברות (מופרדים בפסיקים):",
    placeholder="לדוגמה: בנק דיסקונט, שופרסל, זארה...",
    height=120
)

if st.button("🚀 התחל מחקר מאוחד"):
    if input_text:
        companies = [c.strip() for c in input_text.split(",") if c.strip()]
        
        with st.spinner(f"הסוכן חוקר כעת את {len(companies)} החברות..."):
            try:
                # הרצת המחקר הדו-שלבי
                report = run_multi_company_researcher(companies)
                
                st.subheader("📋 דוח ריכוז סניפים מאוחד")
                st.markdown(report)
                
                st.download_button(
                    label="📥 הורד דוח סופי",
                    data=report,
                    file_name="combined_branch_report.md",
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"אירעה שגיאה בתהליך המחקר: {e}")
    else:
        st.warning("נא להזין לפחות שם של חברה אחת.")

st.divider()
st.caption("Developed with Gemini 2.5 Flash & Vertex AI | 2026 Edition")