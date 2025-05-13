import os
from dotenv import load_dotenv
from datetime import timedelta

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da aplicação
class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de autenticação
    DEFAULT_USERNAME = os.getenv('DEFAULT_USERNAME', 'admin')
    DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD', 'admin123')
    
    # Configurações de validação
    MIN_TEXT_LENGTH = 50
    MAX_TEXT_LENGTH = 5000
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Tipos de peças permitidos
    ALLOWED_CASE_TYPES = [
        "Petição Inicial",
        "Contestação",
        "Recurso",
        "Agravo",
        "Embargos"
    ]
    
    # Configurações da API Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.0-flash'
    GEMINI_MAX_RETRIES = 3
    GEMINI_TIMEOUT = 30
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'
    
    # Configurações de rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Configurações de PDF
    PDFKIT_PATH = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
    PDF_TEMPLATE_DIR = 'templates/pdf' 