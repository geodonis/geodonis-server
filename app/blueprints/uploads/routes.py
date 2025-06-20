from flask import Blueprint, jsonify, request, render_template, current_app
from app.common.utils.standard_exceptions import APIClientError, api_error_response_exception
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields, ValidationError
from flask_jwt_extended import jwt_required

uploads_bp = Blueprint('uploads_bp', __name__, template_folder='templates')

UPLOADS_BASE_FOLDER = 'uploads'
ALLOWED_FILE_TYPES = ['venue_gps_trace']

class UploadFileSchema(Schema):
    file_type = fields.Str(required=True, validate=lambda x: x in ALLOWED_FILE_TYPES)
    file_name = fields.Str(required=True)
    update = fields.Boolean(required=True)

upload_file_schema = UploadFileSchema()

@uploads_bp.route('/uploads/upload-test', methods=['GET'])
@jwt_required()
def upload_test():
    return render_template('uploads/upload_test.html')

@uploads_bp.route('/api/uploads/upload-file', methods=['POST'])
@jwt_required()
def upload_file():
    try:
        # Validate form data
        try:
            data = upload_file_schema.load(request.form)
        except ValidationError as e:
            raise APIClientError(f"Invalid input: {str(e)}") from e # All these were client errors instead of plain exceptions

        file_type = data['file_type']
        file_name = secure_filename(data['file_name'])
        update = data['update']

        if update:
            raise APIClientError("Updates not currently enabled!")

        # Check if file was included in the request
        if 'file' not in request.files:
            raise APIClientError("No file part in the request")
        
        file = request.files['file']
        if file.filename == '':
            raise APIClientError("No file selected for uploading")

        # Check file existence and update flag
        file_storage = current_app.config['FILE_STORAGE']
        folder_key = f"{UPLOADS_BASE_FOLDER}/{file_type}/"
        file_exists = file_storage.file_exists(folder_key, file_name)

        if file_exists and not update:
            raise APIClientError("File already exists and update flag is false")
        if not file_exists and update:
            raise APIClientError("File does not exist and update flag is true")

        # Save the file
        file_storage.save_file_object(folder_key, file_name, file)

        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file_name': file_name,
            'file_type': file_type
        }), 200

    except Exception as e:
        return api_error_response_exception(e)
