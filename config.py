import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_12345_change_in_production'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or None
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or None
    
    # Database Configuration
    DATABASE_FILE = os.environ.get('DATABASE_FILE') or 'ot.db'
    
    @staticmethod
    def init_app(app):
        pass 