import os
from dotenv import load_dotenv

def setup_environment():
    # הגדרות נטפרי
    netfree_path = r'C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt'
    if os.name == 'nt' and os.path.exists(netfree_path):
        os.environ['SSL_CERT_FILE'] = netfree_path
        os.environ['REQUESTS_CA_BUNDLE'] = netfree_path

    load_dotenv()
    return {
        "GEMINI_KEY": os.getenv("GEMINI_API_KEY"),
        "SERPER_KEY": os.getenv("SERPER_API_KEY")
    }