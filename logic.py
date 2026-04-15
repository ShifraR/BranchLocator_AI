import requests
import json

def fetch_search_results(company_name, api_key):
    """מחפש בגוגל ומחזיר תוצאות גולמיות"""
    url = "https://google.serper.dev/search"
    query = f"סניפים של {company_name} בישראל רשימה כתובות"
    payload = {"q": query, "gl": "il", "hl": "iw", "num": 15}
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get('organic', [])

def extract_branches(raw_results, company_name, api_key):
    """שולח את המידע לג'ימיני לחילוץ JSON"""
    context = ""
    for res in raw_results:
        context += f"Source: {res.get('link')}\nInfo: {res.get('snippet')}\n---\n"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    prompt = f"חלץ רשימת סניפים של {company_name} מהטקסט הבא לפורמט JSON בלבד. שדות: שם הסניף, כתובת, עיר, מקור.\n\nטקסט:\n{context}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    
    try:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return []