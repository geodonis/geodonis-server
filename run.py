from app import create_app
import os

FLASK_ENV = os.environ.get('FLASK_ENV', 'no-default')
if FLASK_ENV not in ['production', 'development', 'dev-prod-db']:
    raise ValueError('FLASK_ENV must be "production", "development", or "dev-prod-db"')

SERVICE_PORT = os.environ.get('SERVICE_PORT', -1)
if SERVICE_PORT == -1:
    raise ValueError('SERVICE_PORT must be set to a valid port number')

app = create_app(FLASK_ENV)

print(f"Flask environment: {FLASK_ENV}")
print(f"Session cookie secure: {app.config.get('JWT_COOKIE_SECURE')}")

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=int(SERVICE_PORT)
    )
