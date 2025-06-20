from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import get_jwt
from app.common.utils.standard_exceptions import api_error_response

def admin_required(f):
    """
    A decorator to protect routes that require admin privileges.

    It checks for a valid JWT and then verifies that the 'is_admin' claim
    within the token is set to True.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        # The verify_jwt_in_request() is already implicitly called by jwt_required()
        # which you should use in combination with this decorator on your routes.
        
        # g.current_user is loaded in the @app.before_request hook in __init__.py
        if not g.current_user:
            #error: 'Authentication required'
            return api_error_response('Authentication required', 401)

        claims = get_jwt()
        if claims.get('is_super_user', False):
            return f(*args, **kwargs)
        else:
            # error: 'Admin access required'
            return api_error_response('Admin access required', 403)
    return decorator
