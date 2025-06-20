

I have flask web app that I am updating to go from session based authentication and CSRF tokens placed on the web pages. I am switching to JWT, as described below.

I want to make a modification for better support of (1) long running applications on a web page (like a map editor) and (2) mobile applications.

Server Setup:

- Access control:
    - Use JWT for access control, with Flask-JWT-Extended.
    - Do not use sessions
- Tokens:
    - JWT refresh token: long expiration (30 days?)
    - JWT access token: short expiration (15 minutes?)
- Server Access control actions for web pages:
    - Server places JWT refresh token in HTTP-only cookie.
    - Server places JWT access token placed in HTTP-only cookie.
    - Server places CSRF token placed in plain cookie.
    - The server automatically updates the access token based on the refresh token if the access token expires. (A access failure happens, it is caught by the server, new tokens issued and a redirect is sent to the browser to reissue tye request)
    - Client API calls must access the CSRF token and place it in the request header.
    - SameSite=Lax control is used. This means the browser includes the tokens on all requests originating from my site. It only includes the tokens on requests originating from a remote site if the request changes the page (location) to my site, meaning the browser will be on my site after the request is completed.  
- Access control for mobile applications:
    - Mobile app acquires a JWT refresh and access token through a login endpoint.
    - No csrf token is used.
    - Mobile app puts the access token (in header) on all normal API requests, while it is valid.
    - Mobile app gets a new access token, using the refresh token (in header) and the refresh endpoint, when the access token is about to expire or is expired. (I assume we could implement it either way.)
- General:
    - we can protect sensitive information by requiring "fresh" access tokens, meaning if the access token has been refreshed, it can not be used for these sensitive actions. The user must re-login.

Server configuration includes:
- API authorization for both header and cookie tokens.
- login form for website
- login API for mobile apps

---

I have already updated the files config.py, __init__.py and decorators.py (and run.py). The new files are given below.

config.py
```
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

```

app/__init__.py
```
from flask import Flask, jsonify, request, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request, create_access_token, set_access_cookies
from flask_migrate import Migrate
from config import config
import logging
import os

from app.service_constants import OS_FILES_RELATIVE_BASE_PATH, NETWORK_FILES_RELATIVE_BASE_PATH
from app.models.user import User 

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config[config_name])

    setup_logging(app)
    setup_storage(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # This function is called whenever a protected endpoint is accessed,
    # and will load the user object into the g context variable.
    @app.before_request
    def load_user_from_jwt():
        try:
            # This will raise an exception if a valid JWT is not present
            verify_jwt_in_request(optional=True) 
            user_identity = get_jwt_identity()
            if user_identity:
                # Store user object in Flask's g for the duration of the request
                g.current_user = User.query.get(user_identity)
            else:
                g.current_user = None
        except Exception:
            g.current_user = None


    # This function is called whenever a protected endpoint is accessed,
    # and will return a custom response if the user is not logged in.
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Missing Authorization Header"}), 401
        return redirect(url_for('auth_bp.login', next=request.url))

    # This function is called whenever a protected endpoint is accessed,
    # and will return a custom response if the JWT is invalid.
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        # We are not clearing cookies here, as the user might have a valid refresh token.
        if request.path.startswith('/api/'):
            return jsonify({"error": "Invalid token", "message": str(error)}), 422
        return redirect(url_for('auth_bp.login', next=request.url))

    # Custom expired token handler to auto-refresh for web clients
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        # Check if the request is from a web browser (expects cookies)
        if request.cookies.get('refresh_token_cookie'):
            try:
                # This is a simplified example. In a real app, you would want to
                # use the refresh token to get a new access token.
                # Here we redirect to a refresh endpoint that will handle it.
                return redirect(url_for('auth_bp.refresh_and_retry', original_url=request.url))
            except Exception as e:
                # If refresh fails, redirect to login
                resp = redirect(url_for('auth_bp.login'))
                return resp
        # For API clients (mobile), return a JSON error
        return jsonify({"error": "Token has expired"}), 401

    # blueprints
    from app.blueprints.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Register other blueprints
    from app.blueprints.user.routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from app.blueprints.uploads.routes import uploads_bp
    app.register_blueprint(uploads_bp, url_prefix='/uploads')

    from app import models

    #========= ENABLE REMOTE FILE DIRECTORY FOR MAP APP FILES =============
    if app.config.get('ENABLE_JS_APP_ROUTE'):
        rel_map_app_path = os.environ.get('REL_MAP_APP_PATH', "/static/mapapp")  # default to a local folder if not set
        full_map_app_path = os.path.abspath(rel_map_app_path)

        from flask import send_from_directory

        @app.route('/static/mapapp/<path:filename>')
        def js_app_files(filename):
            return send_from_directory(full_map_app_path, filename)
    #========= END ENABLE REMOTE FILE DIRECTORY FOR MAP APP FILES =============

    return app
    
def setup_logging(app):
    """Configure basic logging to stderr."""
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Clear any existing handlers
    app.logger.handlers.clear()
    
    # Configure stderr handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(app.config.get('LOG_LEVEL', logging.INFO))
    app.logger.addHandler(console_handler)
    app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))
    
    # Log startup message
    app.logger.info("Logging initialized")

def setup_storage(app):
    # set up DB and file storage
    if app.config["STORAGE_SOURCE"] == "production":
        
        raise Exception("Production storage source not implemented yet")
    
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or \
            f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        from app.common.services.file_storage.s3_file_storage import S3FileStorage
        s3_storage = S3FileStorage(
            bucket_name=os.environ.get('AWS_BT_FILES_BUCKET_NAME'),
            read_access_key=os.environ.get('AWS_BT_FILES_READ_ONLY_ACCESS_KEY'),
            read_secret_key=os.environ.get('AWS_BT_FILES_READ_ONLY_SECRET_KEY'),
            write_access_key=os.environ.get('AWS_BT_FILES_READ_WRITE_ACCESS_KEY'),
            write_secret_key=os.environ.get('AWS_BT_FILES_READ_WRITE_SECRET_KEY')
        )

        #app.config['FILE_STORAGE'] = s3_storage

    elif app.config["STORAGE_SOURCE"] == "development":
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL_LOCAL') or \
            f"postgresql://{os.environ.get('DB_USER_LOCAL')}:{os.environ.get('DB_PASSWORD_LOCAL')}@{os.environ.get('DB_HOST_LOCAL')}:{os.environ.get('DB_PORT_LOCAL')}/{os.environ.get('DB_NAME_LOCAL')}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # Set up file storage
        from app.common.services.file_storage.local_file_storage import LocalFileStorage
        os_files_base_path = os.path.join(app.root_path, OS_FILES_RELATIVE_BASE_PATH)
        url_files_base_path = os.path.join(NETWORK_FILES_RELATIVE_BASE_PATH)
        app.config['FILE_STORAGE'] = LocalFileStorage(os_files_base_path, url_files_base_path)

    else:
        raise ValueError("Invalid STORAGE_SOURCE value")
    
```

app/decorators.py
```
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import get_jwt

def admin_required():
    """
    A decorator to protect routes that require admin privileges.

    It checks for a valid JWT and then verifies that the 'is_admin' claim
    within the token is set to True.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # The verify_jwt_in_request() is already implicitly called by jwt_required()
            # which you should use in combination with this decorator on your routes.
            
            # g.current_user is loaded in the @app.before_request hook in __init__.py
            if not g.current_user:
                return jsonify({'error': 'Authentication required'}), 401

            claims = get_jwt()
            if claims.get('is_admin', False):
                return fn(*args, **kwargs)
            else:
                return jsonify({'error': 'Admin access required'}), 403
        return decorator
    return wrapper
```
---

Now I want to write a new auth route.

app/blueprints/auth/routes.py:
```
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlsplit
from app import db
from app.models.user import User

from app.blueprints.auth.forms import LoginForm


auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('auth_bp.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main_bp.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_bp.index'))

```

app/blueprints/auth/forms.py:
```
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

```

In the new auth routes file, include the support for api logins and logouts. (Do not include other things not listed, like password reset. That is handled elsewhere.)

Please let me know if there is any other infomration you need before starting to update these files.

===========================

The base template calls `current_user`. Do we need to update this, or anything else you see in the template?

As you may recall, in `__init__.py`, current_user is assigned to the flask variable `g`. I am not sure if that puts it in the template.


app/templates/base.html
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Geodonis{% endblock %}</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        main {
            flex: 1;
        }
        .navbar-text.welcome-message {
            color: #00008B; /* Dark Blue */
            font-weight: bold;
        }
        #page-error-container {
            padding: 10px 0;
            background-color: #ffeeee;
        }
    </style>
    {% block head %}
        {% if has_api_call %}
        <meta name="csrf-token" content="{{ csrf_token() }}">
        <script src="{{ url_for('static', filename='js/custom_fetch.js') }}"></script>
        {% endif %}
    {% endblock %}
</head>
<body>
    <header>
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container">
                <a class="navbar-brand" href="{{ url_for('main_bp.index') }}">Geodonis</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    {% if current_user.is_authenticated %}
                        <span class="navbar-text welcome-message">
                            {{ current_user.username }}
                        </span>
                    {% endif %}
                    <ul class="navbar-nav ms-auto">
                        {% if current_user.is_authenticated %}
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('main_bp.index') }}">Home</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('user_bp.edit_account') }}">Account</a></li>
                            <li class="nav-item"><a class="nav-link" href="#" onclick="showFeedbackForm()">Contact/Feedback</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('auth_bp.logout') }}">Logout</a></li>
                        {% else %}
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('auth_bp.login') }}">Login</a></li>
                        {% endif %}
                    </ul>
                </div>
            </div>
        </nav>
        <!-- Inline Login Form -->
        <div id="page-error-container" class="container-fluid py-2 text-center" style="display: none;">
        </div>
    </header>

    <main class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        {% endfor %}
        {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer class="bg-light py-3 mt-4">
        <div class="container text-center">
            <p>&copy; 2025 Geodonis. All rights reserved.</p>
        </div>
    </footer>

    <!-- Bootstrap JS and Popper.js -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showFeedbackForm() {
            // Placeholder for feedback form functionality
            alert("Feedback form coming soon. For now, please email your feedback to [email address].");
        }

        function showPageError(errorMsg) {
            const pageErrorContainer = document.getElementById('page-error-container');
            pageErrorContainer.innerHTML = `<span class="text-danger">${errorMsg}</span>`
            pageErrorContainer.style.display = 'block';
        }

        function hidePageError() {
            const pageErrorContainer = document.getElementById('page-error-container');
            pageErrorContainer.innerHTML = '';
            pageErrorContainer.style.display = 'none';
        }
    </script>
    {% block scripts %}
    {% endblock %}
</body>
</html>
```