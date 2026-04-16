
import os
from dotenv import load_dotenv
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration
from vertexai.language_models import TextEmbeddingModel


def initialize_vertex_ai():
    """מאתחל את החיבור ל-Google Cloud ו-Vertex AI"""
    load_dotenv()
    
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_REGION")
    
    # בניית אובייקט ה-Credentials
    credentials_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key": os.getenv("GCP_PRIVATE_KEY", "").replace('\\n', '\n'),
        "client_email": os.getenv("GCP_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    vertexai.init(project=project_id, location=location, credentials=credentials)
    
    return