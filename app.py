import streamlit as st
from logic import run_multi_company_researcher # פה הייבוא תקין!

st.set_page_config(page_title="Branch Researcher AI", page_icon="📍", layout="wide")

st.title("📍 סוכן חוקר: הצלבת סניפים ומקורות")

input_data = st.text_area(
    "הכניסי שמות חברות (מופרדים בפסיקים):",
    placeholder="לדוגמה: בנק דיסקונט, שופרסל...",
    height=100
)

if st.button("🚀 התחל מחקר מוצלב"):
    if input_data:
        companies = [c.strip() for c in input_data.split(",") if c.strip()]
        with st.spinner("חוקר מקורות..."):
            try:
                report = run_multi_company_researcher(companies)
                st.markdown(report)
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("נא להזין חברה.")