from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate
from config import config
import logging

import os

from app.service_constants import OS_FILES_RELATIVE_BASE_PATH, NETWORK_FILES_RELATIVE_BASE_PATH

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
sess = Session()
migrate = Migrate()

def create_app(config_name):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config[config_name])

    setup_logging(app)
    setup_storage(app)

    # Configure session db
    app.config['SESSION_SQLALCHEMY'] = db

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    sess.init_app(app)

    login_manager.login_view = 'auth_bp.login'
    login_manager.login_message_category = 'info'

    # blueprints

    from app.blueprints.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.user.routes import user_bp
    app.register_blueprint(user_bp)

    from app import models

    return app

@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api/') or request.path.startswith('/file/'):
        return jsonify({"error": "Unauthorized"}), 403
    # For non-API routes, do the default redirect
    else:
        return redirect(url_for(login_manager.login_view, next=request.url))
    
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
    