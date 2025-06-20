from flask import Flask, jsonify, request, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, get_jwt_identity, get_jwt, verify_jwt_in_request, create_access_token, set_access_cookies
from flask_migrate import Migrate
from config import config
from app.common.utils.standard_exceptions import api_error_response
import logging
import os

from app.service_constants import OS_FILES_RELATIVE_BASE_PATH, NETWORK_FILES_RELATIVE_BASE_PATH

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
                from app.models.user import User 
                g.current_user = User.query.get(int(user_identity))
            else:
                g.current_user = None
        except Exception:
            # This will be reached anytime the user is not logged in, but I 'm told that is how to do it.
            g.current_user = None

    # This function is called whenever a protected endpoint is accessed,
    # and will return a custom response if the user is not logged in.
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        if request.path.startswith('/api/'):
            # error: "Missing Authorization Header"
            return api_error_response("Missing Authorization Header", 401)
        else:
            return redirect(url_for('auth_bp.login', next=request.url))

    # This function is called whenever a protected endpoint is accessed,
    # and will return a custom response if the JWT is invalid.
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        # We are not clearing cookies here, as the user might have a valid refresh token.
        if request.path.startswith('/api/'):
            # error: "Invalid token"
            error_msg = "Invalid token: " + str(error)
            return api_error_response(error_msg, 422)
        else:
            return redirect(url_for('auth_bp.login', next=request.url))

    # Custom expired token handler to auto-refresh for web clients
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        # Check if the request is from a web browser (expects cookies)
        if request.path.startswith('/api/'):
            # error: "Token has expired"
            return api_error_response("Token has expired", 401)
        else:
            try:
                # This is a simplified example. In a real app, you would want to
                # use the refresh token to get a new access token.
                # Here we redirect to a refresh endpoint that will handle it.
                return redirect(url_for('auth_bp.refresh_and_retry', original_url=request.url))
            except Exception as e:
                # If refresh fails, redirect to login
                resp = redirect(url_for('auth_bp.login'))
                return resp
        

    # blueprints
    from app.blueprints.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Register other blueprints
    from app.blueprints.user.routes import user_bp
    app.register_blueprint(user_bp)

    from app.blueprints.uploads.routes import uploads_bp
    app.register_blueprint(uploads_bp)

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
