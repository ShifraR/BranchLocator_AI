import os
import sys

# --- 1. התיקון ה"גרעיני" לנטפרי (חייב להופיע לפני כל import אחר!) ---
netfree_bundle = r'C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt'

if os.path.exists(netfree_bundle):
    # הגדרת כל משתנה סביבה אפשרי שספריות תקשורת מחפשות
    os.environ['REQUESTS_CA_BUNDLE'] = netfree_bundle
    os.environ['SSL_CERT_FILE'] = netfree_bundle
    os.environ['CURL_CA_BUNDLE'] = netfree_bundle
    os.environ['HTTPLIB2_CA_CERTS'] = netfree_bundle
    
    # התיקון הקריטי עבור gRPC (ג'ימיני) - לפעמים הוא מעדיף סלאשים רגילים
    os.environ['GRPC_DEFAULT_SSL_ROOTS_CERTIFICATES_PATH'] = netfree_bundle.replace('\\', '/')
    
    # הזרקה ישירה לספריית ה-SSL של פייתון (Monkey Patch)
    import ssl
    try:
        orig_create_default_context = ssl.create_default_context
        def netfree_context(*args, **kwargs):
            context = orig_create_default_context(*args, **kwargs)
            context.load_verify_locations(cafile=netfree_bundle)
            return context
        ssl.create_default_context = netfree_context
        print("✅ NetFree Nuclear Patch Applied")
    except Exception as e:
        print(f"⚠️ SSL Patch Error: {e}")
else:
    print(f"❌ שגיאה: תעודת נטפרי לא נמצאה בנתיב המצוין!")

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

# --- פונקציית עזר לחילוץ טקסט בטוח (פותרת את השגיאה שלך) ---
def extract_text(response):
    """מחברת את כל חלקי הטקסט של המודל ליחידה אחת"""
    try:
        parts = [part.text for part in response.candidates[0].content.parts if part.text]
        return "\n".join(parts)
    except Exception:
        return "לא ניתן היה לחלץ טקסט מהתשובה."

# --- 2. כלי גוגל מפות ---
def get_branches_from_maps(query: str):
    """שואב נתונים פיזיים מ-Google Maps API"""
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

# כלי החיפוש החופשי
web_search_tool = Tool.from_dict({"google_search": {}})

# --- 3. לוגיקת המחקר המשולב ---

def run_multi_company_researcher(companies_list):
    """מריץ מחקר שטח משולב על רשימת חברות"""
    
    # מודל א': מפות
    model_maps = GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[maps_tool],
        system_instruction="אתה מומחה לאיתור סניפים במפות. השתמש תמיד בכלי המפות."
    )
    
    # מודל ב': אינטרנט חופשי (כאן קרתה השגיאה)
    model_web = GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[web_search_tool],
        system_instruction="""אתה חוקר אינטרנט. המשימה שלך היא למצוא סניפים ומידע רשמי מאתרי חברות.
        התמקד במציאת רשימת סניפים מעודכנת. החזר תמיד טבלה מסודרת."""
    )

    final_reports = []

    for company in companies_list:
        # א. שלב המפות
        chat = model_maps.start_chat()
        res_maps = chat.send_message(f"מצא סניפים של {company} בישראל")
        
        maps_data = []
        if res_maps.candidates[0].content.parts[0].function_call:
            call = res_maps.candidates[0].content.parts[0].function_call
            maps_data = get_branches_from_maps(call.args["query"])

        # ב. שלב האינטרנט - שימוש בפונקציית העזר extract_text
        web_prompt = f"""
        חפש סניפים של {company} מהאינטרנט ומהאתר הרשמי שלהם.
        הנה מה שמצאנו במפות: {maps_data}.
        חפש סניפים נוספים או אימות לכתובות אלו. 
        החזר טבלה אחת הכוללת: חברה, סניף, כתובת ומקור המידע.
        """
        res_web = model_web.generate_content(web_prompt)
        
        # כאן התיקון! במקום res_web.text אנחנו משתמשים ב-extract_text
        final_text = extract_text(res_web)
        final_reports.append(final_text)

    return "\n\n---\n\n".join(final_reports)