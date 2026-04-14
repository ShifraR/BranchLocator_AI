import os
import requests
import json
from dotenv import load_dotenv

# --- הגדרות נטפרי (הפתרון המוכח שלך) ---
netfree_windows_path = r'C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt'

if os.name == 'nt' and os.path.exists(netfree_windows_path):
    os.environ['SSL_CERT_FILE'] = netfree_windows_path
    os.environ['REQUESTS_CA_BUNDLE'] = netfree_windows_path
    print("✅ NetFree certificate loaded for Windows.")
else:
    print("⚠️ Running in non-Windows environment or certificate not found.")

# 1. טעינת המפתחות
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

def generate_search_queries(company_name):
    """שימוש ב-REST API של ג'מיני כדי לעקוף בעיות SSL של gRPC"""
    print(f"🔍 מייצר שאילתות חיפוש עבור {company_name}...")
    
    model_name = "gemini-flash-latest" 
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    אני צריך לאתר את כל הסניפים של חברת {company_name} בישראל.
    ייצר עבורי 4 שאילתות חיפוש שונות בגוגל שיעזרו לי למצוא רשימות סניפים ממקורות שונים.
    החזר רק רשימה של 4 שאילתות, אחת בכל שורה, ללא טקסט נוסף.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # חילוץ הטקסט מהתשובה של גוגל
        text_response = result['candidates'][0]['content']['parts'][0]['text']
        queries = text_response.strip().split('\n')
        return [q.strip("- *") for q in queries if q.strip()]
    except Exception as e:
        print(f"❌ שגיאה בפנייה לג'מיני: {e}")
        return []

def search_google(query):
    """חיפוש ב-Serper - זה בדרך כלל עובד חלק עם requests"""
    print(f"🌐 מחפש בגוגל: {query}")
    
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "gl": "il",
        "hl": "iw"
    }
    headers = {
        'X-API-KEY': SERPER_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get('organic', [])
    except Exception as e:
        print(f"❌ שגיאה בחיפוש ב-Serper: {e}")
        return []

# --- הרצה ראשית ---
if __name__ == "__main__":
    company = "ארומה"
    
    # שלב א' - ייצור שאילתות
    search_queries = generate_search_queries(company)
    
    if search_queries:
        # שלב ב' - הרצת חיפוש ואיסוף מידע
        all_raw_results = []
        for q in search_queries:
            results = search_google(q)
            all_raw_results.extend(results)
            
        print(f"\n✅ סיימנו! מצאנו {len(all_raw_results)} מקורות מידע גולמיים.")
        
        if all_raw_results:
            print(f"דוגמה למקור שנמצא: {all_raw_results[0].get('title')}")
    else:
        print("❌ לא הצלחנו לייצר שאילתות, בדקי את החיבור או את ה-API Key.")