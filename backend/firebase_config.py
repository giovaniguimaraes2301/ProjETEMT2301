import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import os
from dotenv import load_dotenv
import json

load_dotenv()

def initialize_firebase():
    """Inicializa Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Criar objeto de credenciais a partir das variáveis de ambiente
        service_account_info = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL')}",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(service_account_info)
        initialize_app(cred)
    
    return firestore.client()

# Instância global do Firestore
db = None

def get_firestore_db():
    """Retorna instância do Firestore"""
    global db
    if db is None:
        db = initialize_firebase()
    return db