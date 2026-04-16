import os
import sys
import json
import requests
import numpy as np
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    Part
)
from vertexai.language_models import TextEmbeddingModel

# --- 1. אתחול מערכת ---
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
LOCATION = "us-east1" 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- פונקציית עזר לחילוץ טקסט (מהקוד המקורי שלך) ---
def extract_text(response):
    """מחברת את כל חלקי הטקסט של המודל ליחידה אחת"""
    try:
        parts = [part.text for part in response.candidates[0].content.parts if part.text]
        return "\n".join(parts)
    except Exception:
        return "לא ניתן היה לחלץ טקסט מהתשובה."

# --- 2. כלי גוגל מפות (מהקוד המקורי שלך) ---
def get_branches_from_maps(query: str):
    print(f"\n[מערכת] מחפש במפות: {query}")
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={MAPS_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("results", [])
            return [{"name": r.get("name"), "address": r.get("formatted_address"), "source": "Google Maps"} 
                    for r in results[:5]]
    except Exception as e:
        print(f"Maps Error: {e}")
    return []

maps_tool = Tool(function_declarations=[
    FunctionDeclaration(
        name="get_branches_from_maps",
        description="איתור סניפים וכתובות ב-Google Maps",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    )
])

# כלי החיפוש החופשי (הגרסה המקורית שעבדה לך)
web_search_tool = Tool.from_dict({"google_search": {}})

# --- תוספת: פונקציית סינון כפילויות ע"י Embeddings ---
def filter_duplicates_by_embeddings(branches, threshold=0.92):
    if not branches: return []
    
    print("\n[מערכת] מסנן כפילויות...")
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    addresses = [f"{b.get('city', '')} {b.get('address', '')}" for b in branches]
    embeddings = [e.values for e in model.get_embeddings(addresses)]
    
    unique_branches = []
    indices_to_skip = set()

    for i in range(len(branches)):
        if i in indices_to_skip: continue
        unique_branches.append(branches[i])
        for j in range(i + 1, len(branches)):
            similarity = np.dot(embeddings[i], embeddings[j]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
            )
            if similarity > threshold:
                indices_to_skip.add(j)
                unique_branches[-1]["source"] += f" + {branches[j].get('source', '')}"
                
    return unique_branches

# --- 3. לוגיקת המחקר המשולב ---
def run_multi_company_researcher(companies_list):
    
    model_maps = GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[maps_tool],
        system_instruction="אתה מומחה לאיתור סניפים במפות. השתמש תמיד בכלי המפות."
    )
    
    model_web = GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[web_search_tool],
        system_instruction="""אתה חוקר אינטרנט. המשימה שלך היא למצוא סניפים. 
        החזר אך ורק טקסט בפורמט JSON תקני של מערך אובייקטים. בלי שום מילות הסבר."""
    )

    final_reports = []

    for company in companies_list:
        # א. שלב המפות
        chat = model_maps.start_chat()
        res_maps = chat.send_message(f"מצא סניפים של {company} בישראל")
        
        maps_data = []
        try:
            if res_maps.candidates[0].content.parts[0].function_call:
                call = res_maps.candidates[0].content.parts[0].function_call
                maps_data = get_branches_from_maps(call.args["query"])
        except Exception:
            pass

        # ב. שלב האינטרנט
        web_prompt = f"""
        חפש סניפים של {company} מהאינטרנט. שלב גם את נתוני המפות: {maps_data}.
        החזר אך ורק מערך JSON (ללא Markdown וללא טקסט נוסף) שבו כל אובייקט מכיל:
        "branch_name", "city", "address", "source".
        """
        res_web = model_web.generate_content(web_prompt)
        raw_text = extract_text(res_web)
        
        try:
            # ניקוי עטיפות Markdown למקרה שהמודל הוסיף אותן
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            branches_list = json.loads(clean_json)
            
            # סינון ויצירת הטבלה
            cleaned_branches = filter_duplicates_by_embeddings(branches_list)
            
            report = f"### דוח סניפים: {company}\n| סניף | עיר | כתובת | מקור |\n|---|---|---|---|\n"
            for b in cleaned_branches:
                report += f"| {b.get('branch_name','')} | {b.get('city','')} | {b.get('address','')} | {b.get('source','')} |\n"
            
            final_reports.append(report)
            
        except Exception as e:
            final_reports.append(f"שגיאה בעיבוד {company}: {e}\nפלט גולמי: {raw_text}")

    return "\n\n---\n\n".join(final_reports)
