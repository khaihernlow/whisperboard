"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')

# API Configuration
ATTENDEE_API_KEY = os.getenv("ATTENDEE_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
ATTENDEE_API_BASE = os.getenv("ATTENDEE_API_BASE", "https://app.attendee.dev")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MIRO_ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN")

# Validate required environment variables
if not ATTENDEE_API_KEY or not WEBHOOK_SECRET:
    raise RuntimeError("Set ATTENDEE_API_KEY and WEBHOOK_SECRET env vars first")

# Flask Configuration
class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5005))
    THREADED = True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
