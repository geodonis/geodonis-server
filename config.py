import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # We are doing our own CSRF protection; see the auth blueprint.
    # We are putting the CSRF token in a non-HTTPOnly cookie
    # and expecting it in the request header.
    JWT_COOKIE_CSRF_PROTECT = True 
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_REFRESH_CSRF_HEADER_NAME = "X-CSRF-TOKEN"


    # Configure SameSite for cookies
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_HTTPONLY = True # Refresh and Access tokens are in HttpOnly cookies

    # Path for cookies
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/api/auth/refresh' # Only send refresh token to the refresh endpoint
    

class DevelopmentConfig(Config):
    DEBUG = False  # debug=True interferes with external debugger
    JWT_COOKIE_SECURE = False  # for http access during development
    STORAGE_SOURCE = 'development'
    ENABLE_JS_APP_ROUTE = True  # enable this to serve static files for the map app from the JS_APP_PATH

class DevProdDbConfig(Config):
    DEBUG = False  # debug=True interferes with external debugger
    JWT_COOKIE_SECURE = False  # for http access
    STORAGE_SOURCE = 'production'
    ENABLE_JS_APP_ROUTE = True  # enable this to serve static files for the map app from the JS_APP_PATH

class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True
    STORAGE_SOURCE = 'production'
    ENABLE_JS_APP_ROUTE = False  # disable external access to static files for production!

config = {
    'development': DevelopmentConfig,
    'dev-prod-db': DevProdDbConfig,
    'production': ProductionConfig,
}
