"""Configuration file for the LLM Analysis Quiz project."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-from-google-form')
    EMAIL = os.getenv('EMAIL', 'your-email@example.com')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Timeout Configuration
    QUIZ_TIMEOUT = 180  # 3 minutes in seconds
    REQUEST_TIMEOUT = 30
    
    # Browser Configuration
    HEADLESS = os.getenv('HEADLESS', 'True').lower() == 'true'
    BROWSER_TYPE = os.getenv('BROWSER_TYPE', 'chromium')
    
    # File Storage
    TEMP_DIR = os.getenv('TEMP_DIR', './temp')
    MAX_FILE_SIZE = 1024 * 1024
    
    @staticmethod
    def validate():
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'your-secret-from-google-form':
            print("WARNING: Using default SECRET_KEY. Please update in .env file")
