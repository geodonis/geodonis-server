import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
    
    # Session configuration
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY = None  # This will be set in create_app
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # TBD: add scheduler configuration for periodic tasks like session cleanup and reset password token cleanup.

class DevelopmentConfig(Config):
    DEBUG = False # debug=True interferes with external debugger
    SESSION_COOKIE_SECURE = False # for http access
    STORAGE_SOURCE = 'development'
    ENABLE_JS_APP_ROUTE = True # enable this to serve static files for the map app from the JS_APP_PATH

    # SAVE_EXERCISE_AUDIO = True #enable this to save audio files for exercises

class DevProdDbConfig(Config):
    DEBUG = False # debug=True interferes with external debugger
    SESSION_COOKIE_SECURE = False # for http access
    STORAGE_SOURCE = 'production'
    ENABLE_JS_APP_ROUTE = True # enable this to serve static files for the map app from the JS_APP_PATH

class ProductionConfig(Config):
    DEBUG = False
    STORAGE_SOURCE = 'production'
    ENABLE_JS_APP_ROUTE = False # disable external access to static files for production!

config = {
    'development': DevelopmentConfig,
    'dev-prod-db': DevProdDbConfig,
    'production': ProductionConfig
}