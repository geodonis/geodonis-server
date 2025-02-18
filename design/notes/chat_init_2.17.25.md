# 2/17/25 System Setup

I'm creating a new flask application and I want to base the system roughly on an older application I have. Below are some setup files from the older application.

A big change between the new application and the old application is that the old application strictly uses http only cookies for access whereas the new system will use http only cookies for web pages and also allow for tokens, of some kind to be determined, for mobile api access. Note that API access from web pages should use the http only cookies.

The new system will be using a slightly different data model for users and user management and sharing.

I'd like you to review the files below and tell me what modifications you think will be necessary. Please be specific about libraries and settings that should be added for the new application. Also let me know if the change in user data model has any implications on the files below.

run.py
```
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
```

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
    
    # Session configuration
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY = None  # This will be set in create_app
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # TBD: add scheduler configuration for periodic tasks like session cleanup and reset password token cleanup.

class DevelopmentConfig(Config):
    DEBUG = False # debug=True interferes with external debugger
    SESSION_COOKIE_SECURE = False # for http access
    STORAGE_SOURCE = 'development'

    # SAVE_EXERCISE_AUDIO = True #enable this to save audio files for exercises

class DevProdDbConfig(Config):
    DEBUG = False # debug=True interferes with external debugger
    SESSION_COOKIE_SECURE = False # for http access
    STORAGE_SOURCE = 'production'

class ProductionConfig(Config):
    DEBUG = False
    STORAGE_SOURCE = 'production'

config = {
    'development': DevelopmentConfig,
    'dev-prod-db': DevProdDbConfig,
    'production': ProductionConfig
}
```

app/_init_.py

```
from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate
from config import config
from datetime import timedelta

import os

from app.service_constants import OS_FILES_RELATIVE_BASE_PATH, NETWORK_FILES_RELATIVE_BASE_PATH
from app.common.services.file_storage.local_file_storage import LocalFileStorage
from app.common.services.file_storage.s3_file_storage import S3FileStorage

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
sess = Session()
migrate = Migrate()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # set up DB and file storage
    if app.config["STORAGE_SOURCE"] == "production":
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or \
            f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        s3_storage = S3FileStorage(
            bucket_name=os.environ.get('AWS_BT_FILES_BUCKET_NAME'),
            read_access_key=os.environ.get('AWS_BT_FILES_READ_ONLY_ACCESS_KEY'),
            read_secret_key=os.environ.get('AWS_BT_FILES_READ_ONLY_SECRET_KEY'),
            write_access_key=os.environ.get('AWS_BT_FILES_READ_WRITE_ACCESS_KEY'),
            write_secret_key=os.environ.get('AWS_BT_FILES_READ_WRITE_SECRET_KEY')
        )

        app.config['FILE_STORAGE'] = s3_storage

    elif app.config["STORAGE_SOURCE"] == "development":
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL_LOCAL') or \
            f"postgresql://{os.environ.get('DB_USER_LOCAL')}:{os.environ.get('DB_PASSWORD_LOCAL')}@{os.environ.get('DB_HOST_LOCAL')}:{os.environ.get('DB_PORT_LOCAL')}/{os.environ.get('DB_NAME_LOCAL')}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # Set up file storage
        os_files_base_path = os.path.join(app.root_path, OS_FILES_RELATIVE_BASE_PATH)
        url_files_base_path = os.path.join(NETWORK_FILES_RELATIVE_BASE_PATH)
        app.config['FILE_STORAGE'] = LocalFileStorage(os_files_base_path, url_files_base_path)

    else:
        raise ValueError("Invalid STORAGE_SOURCE value")
    
    # Configure session lifetime
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=120)
    #app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = db

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    sess.init_app(app)

    login_manager.login_view = 'auth_bp.login'
    login_manager.login_message_category = 'info'

    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.content.routes import content_bp
    app.register_blueprint(content_bp)

    from app.blueprints.parrot.routes import parrot_bp
    app.register_blueprint(parrot_bp)

    from app.blueprints.passages.routes import passages_bp
    app.register_blueprint(passages_bp)

    from app.blueprints.prompt_dev.routes import prompt_dev_bp
    app.register_blueprint(prompt_dev_bp)

    from app.blueprints.word_list.routes import word_list_bp
    app.register_blueprint(word_list_bp)

    from app import models

    return app

@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api/') or request.path.startswith('/file/'):
        return jsonify({"error": "Unauthorized"}), 403
    # For non-API routes, do the default redirect
    else:
        return redirect(url_for(login_manager.login_view, next=request.url))
```

======================

Below are some concrete recommendations and modifications you should consider when adapting the old code for your new application:

---

### 1. **Token-Based Authentication**

Since you now want to support token-based access (for mobile APIs) alongside the existing cookie‐based sessions, you’ll need to introduce a token authentication library. A common choice is **[Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/en/stable/)**.

**Modifications:**

- **Installation:**  
  ```bash
  pip install Flask-JWT-Extended
  ```

- **Configuration:**  
  In your `config.py` (or a dedicated config section), add settings for JWT tokens. For example:
  
  ```python
  class Config:
      # ... existing settings
      
      # JWT configuration for token-based authentication
      JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'default-jwt-secret'
      JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
      JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
      # Optionally specify where the JWT should be looked for:
      JWT_TOKEN_LOCATION = ['headers']
  ```
  
- **Initialization:**  
  In your `app/__init__.py`, import and initialize the JWT extension:
  
  ```python
  from flask_jwt_extended import JWTManager
  jwt = JWTManager()
  
  def create_app(config_name):
      app = Flask(__name__)
      app.config.from_object(config[config_name])
      
      # ... existing configuration
      
      # Initialize JWT manager
      jwt.init_app(app)
      
      # ... continue with your blueprint registrations and other initializations
      return app
  ```

- **API Endpoints:**  
  Create new endpoints (or a separate blueprint) for mobile API access that issue and require tokens. Use decorators like `@jwt_required()` on endpoints that need token authentication.

- **Cookie vs. Token Routes:**  
  Ensure that your routing is set up so that web page routes continue to use the http-only cookie session, while API routes can be accessed with JWTs. (Your current `login_manager.unauthorized_handler` already distinguishes between API (`/api/`) and other routes.)

---

### 2. **User Data Model Changes**

A revised user model (with updated fields, relationships, or methods) will have several implications:

- **Login Manager:**  
  The `user_loader` callback (which is likely defined in your user model or elsewhere) must now reference the new user model. Make sure that:
  
  ```python
  @login_manager.user_loader
  def load_user(user_id):
      return NewUserModel.query.get(int(user_id))
  ```
  
  (Adjust for any differences in primary key type or lookup logic.)

- **Token Identity Callback:**  
  If you use Flask-JWT-Extended, you may need to define additional callbacks to translate between the JWT identity and your new user model (for example, via `@jwt.user_lookup_loader`).

- **Database Migrations:**  
  With the new user schema, you’ll need to generate and run a migration script (using **Flask-Migrate**) that reflects these changes.

- **User Serialization:**  
  If any endpoints (especially token endpoints) serialize user information, ensure they correctly map to the new user model’s structure.

---

### 3. **Additional Library/Settings Considerations**

- **CORS:**  
  Since mobile API requests might come from different origins than your web front-end, consider adding **[Flask-CORS](https://flask-cors.readthedocs.io/en/latest/)** to manage cross-origin requests.  
  **Installation:**
  ```bash
  pip install Flask-Cors
  ```
  **Usage in `app/__init__.py`:**
  ```python
  from flask_cors import CORS
  # After app is created:
  CORS(app, resources={r"/api/*": {"origins": "*"}})  # Adjust origins as needed.
  ```

- **Scheduler Configuration:**  
  As noted in your comments, you might eventually want to add periodic tasks (e.g., for session cleanup or expired token cleanup). A library such as **[APScheduler](https://apscheduler.readthedocs.io/en/stable/)** or **Celery** can be integrated for this purpose.

- **Environment Specific Configurations:**  
  Make sure that the JWT configuration (and any other security-related settings) are tightened in production. For example, ensure that both `SESSION_COOKIE_SECURE` and `JWT_SECRET_KEY` are set appropriately in production.

---

### 4. **Impact on Existing Files**

- **`run.py`:**  
  Likely no changes are needed here aside from ensuring that any new environment variables (like `JWT_SECRET_KEY`) are set. The structure for starting the app remains the same.

- **`config.py`:**  
  Add the JWT-related settings and possibly any other new configurations (e.g., for CORS or token expiry). The new user model itself does not directly affect this file unless you need to pass specific settings to the user management system.

- **`app/__init__.py`:**  
  You’ll need to add the initialization of any new libraries (JWTManager, CORS, etc.) and possibly modify any user-loading callbacks to work with your new data model. Also, verify that any CSRF or session-related settings still match your desired security model given the dual authentication methods.

---

### Summary

1. **Token Authentication:**  
   - Add **Flask-JWT-Extended** with appropriate configuration and initialization.
   - Create token-based login endpoints and protect API routes with `@jwt_required()`.

2. **User Model Updates:**  
   - Update the `user_loader` callback and any JWT identity callbacks to reflect changes in your user data model.
   - Generate new database migration scripts to incorporate the new user schema.

3. **Other Enhancements:**  
   - Consider adding **Flask-CORS** for API access from mobile devices.
   - Plan for scheduled tasks (with APScheduler or Celery) if you need regular cleanup tasks.

By following these steps and modifications, you should be able to support both the existing web-based cookie sessions and the new token-based API access while accommodating your updated user data model.

========================

Reading your response I'm not sure if I was clear about one thing. I would like the endpoints in the api to be accessible both via token or HTTP only cookie. From reading a response I wasn't sure if you were thinking there would be different endpoints for tokens versus cookies.

Along those lines, if I remember correctly, the old application had settings so the API could only be accessed from web pages with the proper domain. Do I have that right? Is that something you can see in the settings? If so, that would certainly need to be changed for mobile requests. Does this have security implications for the website requests? If this is any problem, could we restrict the http cookies to only come from the proper domain and allow more free access for the token requests. (Also let me know if this line of questioning even makes sense?)

=======================

Your clarification makes sense. In a system where both cookies and tokens are accepted on the same endpoints, you’ll need to design your authentication logic to support “dual authentication” on a per-request basis. Here are some detailed points addressing your concerns:

---

### 1. **Dual Authentication on the Same Endpoints**

- **Unified Endpoints:**  
  You can certainly use the same API endpoints for both cookie-based and token-based authentication. The key is to write your authentication layer (or decorators) so that they check for either a valid session (via Flask-Login or similar) or a valid JWT (via Flask-JWT-Extended or your chosen token library).

- **Custom Decorators or Middleware:**  
  You might create a custom decorator that first checks if the user is logged in via a session cookie. If not, it then checks for a valid token in the request (often provided in the `Authorization` header). For example:
  
  ```python
  from functools import wraps
  from flask import request, jsonify
  from flask_login import current_user, login_required
  from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

  def dual_auth_required(fn):
      @wraps(fn)
      def wrapper(*args, **kwargs):
          # First, check if there is a logged-in user via session
          if current_user and current_user.is_authenticated:
              return fn(*args, **kwargs)
          
          # Otherwise, attempt JWT auth
          try:
              verify_jwt_in_request()
              # Optionally, set current_user if needed from the token identity
          except Exception as e:
              return jsonify({"error": "Unauthorized"}), 401

          return fn(*args, **kwargs)
      return wrapper
  ```

- **Implementation Note:**  
  While this approach works, ensure that the dual check does not introduce vulnerabilities—for instance, by accidentally accepting expired or otherwise invalid tokens.

---

### 2. **Domain Restrictions on API Access**

- **Old Application Behavior:**  
  In your previous application, it seems that API endpoints were only accessible via the proper domain—this was likely enforced by cookie settings (such as `SESSION_COOKIE_SAMESITE = 'Strict'` and possibly a `SESSION_COOKIE_DOMAIN` if set) and maybe additional server-side checks.

- **What the Settings Show:**  
  In your provided settings, the cookie configurations (like `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_SAMESITE`) hint at a policy that prevents cross-site usage, which indirectly limits API access to web pages from the same domain. However, there isn’t an explicit domain restriction in the code you posted (e.g., a `SESSION_COOKIE_DOMAIN` setting).  
  This suggests that while your cookies are protected from being accessed cross-site (helping prevent CSRF), the API endpoints themselves may have been indirectly restricted because the browser wouldn’t send cookies on cross-domain requests.

- **Adjusting for Mobile:**  
  Mobile applications typically don’t rely on browser cookies, so they’d use tokens. To accommodate both:
  
  - **For Cookies (Web):**  
    You can continue to enforce strict cookie policies (including a restricted domain, if needed) to ensure that web sessions remain secure.
    
  - **For Tokens (Mobile/API):**  
    Tokens can be validated independently of the domain since they’re sent in the header. This means you can relax domain restrictions on token-based requests without affecting the secure handling of session cookies.

- **Security Implications:**  
  Allowing tokens to be accepted from any domain does widen the potential attack surface slightly, so it’s crucial to ensure that:
  
  - Tokens are short-lived and securely signed.
  - HTTPS is enforced so that tokens aren’t intercepted.
  - You might also implement CORS policies (using something like **Flask-CORS**) that allow specific origins for your API endpoints.
  
  This separation means that your website (using cookies) remains locked down to the proper domain, while token-based authentication for mobile can be more flexible. In practice, this separation is common—web sessions remain tightly controlled, while API tokens are designed for broader usage.

---

### Summary

- **Dual Access on Endpoints:**  
  Use a custom authentication check that first validates a session cookie and then checks for a JWT if no valid session is found. This allows the same endpoints to be accessed via either method.

- **Domain Restrictions:**  
  Your old settings enforce strict cookie policies, which means that only web pages from the proper domain can send the http-only cookies. For mobile clients using tokens, these restrictions can be relaxed. Just ensure that you maintain proper security on tokens (short expiration, secure signing, HTTPS enforcement) and possibly use CORS to restrict origins if necessary.

- **No Need for Separate Endpoints:**  
  The same endpoint can support both authentication mechanisms, provided your logic distinguishes between the two and handles them correctly.

This design keeps your web application secure by tightly controlling cookie-based sessions while providing flexibility for mobile devices to authenticate using tokens.

===============================

I want to take my first step towards coding this system. I want to take a minimal first step. When I finish I do not intend to have a viable service but just the first step towards making a viable service. I'm thinking of setting up those three pages we've been discussing including the addition of tokens for example and then adding minimal additional content.

1. Maybe I could have a single web page with no access restrictions. I would like the web page at "app/templates/main/index.html".

2. It looks like I do need a user since that's referenced from the three pages.

I want to use a postgres database and this User model in the file "app/models/User.py"

- **Users Table**:
    - id (primary key)
    - username (unique)
    - email (unique)
    - password_hash
    - status (options: [active, suspended, deleted])
    - is_super_user (boolean, default false - true intended for single main system user)
    - created_at
    - updated_at

---

What else is needed so the system will run and the single page is accessible?

============================

Below is a checklist and some example code snippets that you can use as a minimal “first step” to have a running Flask application that meets your criteria.

---

## 1. **Project Structure**

Your project directory might look like this:

```
your_app/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── User.py
│   ├── blueprints/
│   │   └── main/
│   │       ├── __init__.py
│   │       └── routes.py
│   └── templates/
│       └── main/
│           └── index.html
├── config.py
└── run.py
```

---

## 2. **User Model**

In `app/models/User.py`, create your User model. For example:

```python
from datetime import datetime
from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, suspended, deleted
    is_super_user = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'
```

*Notes:*
- We’re inheriting from `UserMixin` so that Flask-Login functions correctly.
- The table name is set to `"users"`.

---

## 3. **Main Blueprint**

In `app/blueprints/main/routes.py`, define a minimal route for your public page:

```python
from flask import Blueprint, render_template

main_bp = Blueprint('main_bp', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    return render_template('main/index.html')
```

Make sure you register this blueprint in your `app/__init__.py` (your code already shows registration, so verify that `main_bp` is imported correctly).

*Example snippet from `app/__init__.py`:*
```python
from app.blueprints.main.routes import main_bp
app.register_blueprint(main_bp)
```

---

## 4. **Template**

Create a simple HTML file at `app/templates/main/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome</title>
</head>
<body>
    <h1>Welcome to the Minimal Flask App</h1>
    <p>This is an unprotected page accessible by anyone.</p>
</body>
</html>
```

---

## 5. **Database Setup**

Since you want to use Postgres:

- **Environment Variables:**  
  Ensure that your environment has the necessary variables set (or adjust your connection strings in `config.py`). For example, you might need:
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_HOST`
  - `DB_PORT`
  - `DB_NAME`
  
  In your `config.py`, the production configuration builds the URI using these variables:
  
  ```python
  app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or \
      f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
  ```

- **Migrations:**  
  You already have Flask-Migrate configured. Now you can run:
  
  ```bash
  flask db init
  flask db migrate -m "Initial migration: add users table"
  flask db upgrade
  ```

  (Or use `python run.py` if your app is set up to work with the Flask CLI.)

---

## 6. **Additional Minimal Setup**

- **User Loader:**  
  To make Flask-Login work, you need a `user_loader` callback. You can add this to your `app/__init__.py` (or in a separate file):

  ```python
  from app.models.User import User
  from app import login_manager

  @login_manager.user_loader
  def load_user(user_id):
      return User.query.get(int(user_id))
  ```

- **Tokens (Minimal):**  
  Since you plan to support tokens eventually, you might want to install Flask-JWT-Extended now and add a basic configuration in your `config.py`. (You can keep the endpoints and configuration minimal for now.)

  ```python
  # In config.py, add to the Config class:
  JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret')
  ```

  And in `app/__init__.py` initialize it:
  
  ```python
  from flask_jwt_extended import JWTManager
  jwt = JWTManager()
  jwt.init_app(app)
  ```

  No endpoints need to be JWT protected yet if you’re not implementing token-based access fully at this step.

---

## 7. **Running the App**

- **run.py** is already set up to create the app and run it on the defined port. Make sure your environment variables (like `FLASK_ENV`, `SERVICE_PORT`, and database connection details) are set.

- **Dependencies:**  
  Ensure you have installed required packages:
  
  ```bash
  pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-Login Flask-WTF Flask-Session psycopg2-binary python-dotenv Flask-JWT-Extended
  ```

- **Start the App:**  
  Run the app with:
  
  ```bash
  python run.py
  ```

Then visit `http://localhost:<SERVICE_PORT>/` to see your minimal page.

---

## Summary

For a minimal first step, you’ll need:

1. **User Model** in `app/models/User.py` (with the specified fields).
2. **Blueprint and Route** in `app/blueprints/main/routes.py` that renders the template.
3. **Template File** at `app/templates/main/index.html`.
4. **Database Configuration** in `config.py` and environment variables for Postgres.
5. **Database Migration Commands** to create your `users` table.
6. **User Loader and JWT Initialization** in `app/__init__.py` to support login and future token-based access.
7. **run.py** to create and run the application.

With these components in place, you’ll have a minimal, accessible service that lays the groundwork for further development (such as dual authentication support).

=========================
==========================
==========================

QUESTION ABOUT IMPLEMENTING DUAL ACCESS:

When I have to implement an api endpoint that accepts both cookie authentication and token authentication what exactly will I need to do, supposing I am using the existing cookie libraries and the recommended jwt library.

=============

To support both cookie-based (via Flask-Login) and token-based (via Flask-JWT-Extended) authentication on the same endpoint, you’ll need to create a strategy that checks for one method and then the other. In practice, you can:

1. **Check for a Valid Cookie Session:**  
   Use Flask-Login’s `current_user` to see if the user is already authenticated through a cookie.

2. **Check for a Valid JWT Token:**  
   If the cookie isn’t present or the user isn’t authenticated, check if the request includes a valid JWT token. With Flask-JWT-Extended, you can use a method like `verify_jwt_in_request(optional=True)` to optionally validate a token.

3. **Combine Both Checks:**  
   Write a custom decorator (or inline logic) that attempts one method and falls back to the other.

Below is an example of a custom decorator that accomplishes this:

---

```python
from functools import wraps
from flask import jsonify
from flask_login import current_user
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def dual_auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # First, try cookie authentication
        if current_user.is_authenticated:
            return fn(*args, **kwargs)
        
        # Next, try token authentication
        try:
            # This will verify the token if it's present; using optional=True prevents an error if not present
            verify_jwt_in_request(optional=True)
        except Exception:
            # If token verification raises an exception, we'll consider the user unauthenticated
            pass
        
        jwt_identity = get_jwt_identity()
        if jwt_identity:
            # Optionally, you can load the user from the database using the identity here if needed
            return fn(*args, **kwargs)
        
        # If neither method authenticates the user, return an unauthorized error.
        return jsonify({"error": "Unauthorized"}), 403
    
    return wrapper
```

---

### How to Use the Decorator

Simply apply the decorator to your API endpoint:

```python
from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/protected', methods=['GET'])
@dual_auth_required
def protected_endpoint():
    # This code is reached only if the user is authenticated via cookie or token.
    return jsonify({"message": "Access granted"})
```

### Key Points

- **Order of Checks:**  
  The decorator first checks if `current_user.is_authenticated` is `True` (cookie-based auth). If not, it then tries to validate a JWT token.

- **Optional JWT Verification:**  
  The use of `verify_jwt_in_request(optional=True)` means that if no token is present, it won’t immediately abort the request with an error. Instead, it lets you check `get_jwt_identity()` afterward to decide if token authentication was successful.

- **Loading the User:**  
  If your endpoint later requires a full user object (beyond what the JWT provides), you might need to load the user from your database using the JWT identity.

- **Error Handling:**  
  If neither method authenticates the user, the decorator returns a 403 response with an “Unauthorized” message.

### Final Thoughts

By using this approach, you can seamlessly support both types of authentication on your API endpoints. Just ensure that your login and token issuance endpoints are appropriately set up, and that your JWT configuration in your `config.py` is correctly defined.

This method keeps the implementation straightforward and flexible, allowing your API endpoints to work for both web-based sessions and mobile (or other) clients using JWT tokens.

===========================



