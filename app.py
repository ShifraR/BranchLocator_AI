import streamlit as st
import pandas as pd
from config import setup_environment
from logic import fetch_search_results, extract_branches_raw, filter_with_embeddings

keys = setup_environment()

st.set_page_config(page_title="Branch Locator - Embedding AI", layout="wide")
st.markdown("<style>.main { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

st.title("🏙️ מאתר סניפים עם סינון Embeddings")

company = st.text_input("שם החברה:")

if st.button("התחל תהליך חכם"):
    if company:
        with st.status("מפעיל אלגוריתם סינון וקטורי...", expanded=True) as status:
            st.write("🔍 שלב 1: איסוף מידע גולמי...")
            raw_data = fetch_search_results(company, keys["SERPER_KEY"])
            
            st.write("🧠 שלב 2: חילוץ ישויות (Entity Extraction)...")
            all_branches = extract_branches_raw(raw_data, company, keys["GEMINI_KEY"])
            
            st.write(f"📏 שלב 3: חישוב מרחקים וקטוריים לסינון {len(all_branches)} סניפים...")
            final_branches = filter_with_embeddings(all_branches, keys["GEMINI_KEY"])
            
            status.update(label="הסינון הושלם!", state="complete", expanded=False)

        if final_branches:
            st.success(f"נשארו {len(final_branches)} סניפים ייחודיים לאחר סינון דמיון.")
            st.dataframe(pd.DataFrame(final_branches), use_container_width=True)