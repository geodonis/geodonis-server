from functools import wraps
from flask import abort, jsonify
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """
        Requires the user have the "admin" role.
        """
        if not current_user.is_authenticated or not current_user.is_super_user:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function
