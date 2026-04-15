import requests
import json
import numpy as np
import streamlit as st

def fetch_search_results(company_name, api_key):
    url = "https://google.serper.dev/search"
    query = f"רשימת סניפים {company_name} ישראל כתובות"
    payload = {"q": query, "gl": "il", "hl": "iw", "num": 15}
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get('organic', [])

def extract_branches_raw(raw_results, company_name, api_key):
    """חילוץ ראשוני של רשימה (עם כפילויות)"""
    context = ""
    for res in raw_results:
        context += f"Source: {res.get('link')}\nText: {res.get('snippet')}\n---\n"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    prompt = f"חלץ רשימת סניפים של {company_name} ל-JSON. אל תסנן כפילויות, רק תחלץ מה שכתוב. שדות: שם הסניף, כתובת, עיר, מקור.\n\n{context}"
    
    response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    try:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw_text.replace("```json", "").replace("```", "").strip())
    except: return []

def get_embedding(text, api_key):
    """הופך טקסט לוקטור עם מעבר לגרסה יציבה (v1) וגיבוי למודל קודם"""
    # שינוי ל-v1 במקום v1beta
    base_url = "https://generativelanguage.googleapis.com/v1/models/"
    model_name = "text-embedding-004" # המודל הכי חדש
    fallback_model = "embedding-001"   # המודל היציב הקודם (ליתר ביטחון)
    
    url = f"{base_url}{model_name}:embedContent?key={api_key}"
    
    payload = {
        "model": f"models/{model_name}",
        "content": {"parts": [{"text": text}]}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        # אם המודל החדש לא נמצא, ננסה אוטומטית את הישן יותר
        if 'error' in res_json:
            # ניסיון שני עם מודל גיבוי
            url_fallback = f"{base_url}{fallback_model}:embedContent?key={api_key}"
            payload["model"] = f"models/{fallback_model}"
            response = requests.post(url_fallback, json=payload, timeout=30)
            res_json = response.json()
            
            if 'error' in res_json:
                # אם גם זה נכשל, נחזיר None
                return None
            
        return res_json['embedding']['values']
    except:
        return None
    
def cosine_similarity(v1, v2):
    """חישוב דמיון בין שני וקטורים"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def filter_with_embeddings(branches, api_key, threshold=0.92):
    """סינון כפילויות עם הגנה מפני ערכי None"""
    if not branches: return []
    
    unique_branches = []
    embeddings = []

    for branch in branches:
        fingerprint = f"{branch.get('שם הסניף', '')} {branch.get('כתובת', '')}"
        current_emb = get_embedding(fingerprint, api_key)
        
        # אם ה-API נכשל, אנחנו לא רוצים שהקוד יקרוס
        if current_emb is None:
            unique_branches.append(branch) # מוסיפים בכל זאת כדי לא לאבד מידע
            continue
            
        is_duplicate = False
        for saved_emb in embeddings:
            if cosine_similarity(current_emb, saved_emb) > threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_branches.append(branch)
            embeddings.append(current_emb)
            
    return unique_branches



