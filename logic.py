import os
import requests
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    Part,
    grounding 
)

# --- 1. אתחול מערכת ---
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
LOCATION = "us-east1" 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- 2. כלי גוגל מפות (Function) ---
def get_branches_from_maps(query: str):
    """שואב נתונים פיזיים מ-Google Maps API"""
    print(f"\n[שלב 1] מחפש במפות: {query}")
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={MAPS_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("results", [])
            return [
                {"name": r.get("name"), "address": r.get("formatted_address")} 
                for r in results[:5]
            ]
    except Exception as e:
        print(f"Error: {e}")
    return []

maps_tool_decl = FunctionDeclaration(
    name="get_branches_from_maps",
    description="מציאת כתובות ומיקומים פיזיים מתוך Google Maps",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
)

# הגדרת הכלים בנפרד
maps_tool = Tool(function_declarations=[maps_tool_decl])
# שימוש בפורמט הדיקשנרי שעוקף באגים ב-SDK
search_tool = Tool.from_dict({"google_search": {}})

# --- 3. לוגיקת הסוכן הדו-שלבי ---

def run_multi_company_researcher(companies_list):
    """סוכן המבצע מחקר בשני שלבים: מפות ואז אימות באינטרנט"""
    
    # שלב 1: איסוף נתונים ממפות
    model_maps = GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[maps_tool],
        system_instruction="אתה סוכן שאוסף כתובות בלבד בעזרת כלי המפות."
    )
    
    all_raw_data = []
    for company in companies_list:
        chat = model_maps.start_chat()
        # כאן chat.send_message עובד כי זה אובייקט מסוג ChatSession
        response = chat.send_message(f"מצא סניפים של {company}")
        
        if response.candidates[0].content.parts[0].function_call:
            call = response.candidates[0].content.parts[0].function_call
            results = get_branches_from_maps(call.args["query"])
            all_raw_data.append({"company": company, "branches": results})
    
    # שלב 2: הצלבת נתונים מול האינטרנט
    model_search = GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[search_tool],
        system_instruction="""אתה חוקר נתונים. קיבלת רשימת סניפים מהמפות. 
        השתמש בחיפוש גוגל כדי למצוא את האתר הרשמי ולאמת את המידע.
        החזר טבלה סופית עם: חברה, סניף, כתובת, ומקור (לדוגמה: 'מפות + אתר רשמי')."""
    )
    
    final_prompt = f"הנה הנתונים מהמפות: {all_raw_data}. בצע הצלבה מול אתרי החברות והחזר דוח סופי."
    
    # התיקון כאן: שימוש ב-generate_content במקום send_message
    final_response = model_search.generate_content(final_prompt)
    
    return final_response.text