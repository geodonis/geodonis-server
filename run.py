from app import create_app
import os

FLASK_ENV = os.environ.get('FLASK_ENV', 'default')
if FLASK_ENV != 'production' and FLASK_ENV != 'development' and FLASK_ENV != 'dev-prod-db':
    raise ValueError('FLASK_ENV must be either "production" or "development" or "dev-prod-db"')

SERVICE_PORT = os.environ.get('SERVICE_PORT', -1)
if SERVICE_PORT == -1:
    raise ValueError('SERVICE_PORT must be set to a valid port number')

app = create_app(FLASK_ENV)

print(FLASK_ENV)

print(f"session cookie secure: {app.config['SESSION_COOKIE_SECURE']}")

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=SERVICE_PORT
    )