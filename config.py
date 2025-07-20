import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_change_this_in_production'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or 'your_google_client_id_here'
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or 'your_google_client_secret_here'
    
    # Database Configuration
    DATABASE_FILE = os.environ.get('DATABASE_FILE') or 'ot.db'
    
    @staticmethod
    def init_app(app):
        pass 