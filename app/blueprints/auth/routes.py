from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response, g
from urllib.parse import urlsplit
from app import db
from app.models.user import User
from app.blueprints.auth.forms import LoginForm
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    verify_jwt_in_request,
    get_jwt
)

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')

# ===================================================================================
# Web Application Routes (Cookie-based)
# ===================================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles the login process for web users.
    On GET, it displays the login form.
    On POST, it validates credentials, and if successful, sets JWTs in HttpOnly cookies.
    """
    # If there is a token, redirect if we have a valid user
    if g.current_user:
        flash("Already logged in.", 'success')
        return redirect(url_for('main_bp.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Create tokens for the user
            # Add custom claims, for example, to identify admin users.
            additional_claims = {"is_super_user": user.is_super_user}
            access_token = create_access_token(identity=str(user.id), fresh=True, additional_claims=additional_claims)
            refresh_token = create_refresh_token(identity=str(user.id))

            # Determine the redirect target
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main_bp.index')
            
            # Create a response object and set cookies
            resp = make_response(redirect(next_page))

            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)

            flash('Login successful!', 'success')
            return resp
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('auth_bp.login'))
            
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
def logout():
    """
    Handles the logout process for web users.
    It clears the JWT cookies from the browser.
    """
    resp = make_response(redirect(url_for('main_bp.index')))
    unset_jwt_cookies(resp)
    flash('You have been successfully logged out.', 'success')
    return resp

@auth_bp.route('/refresh-and-retry')
@jwt_required(refresh=True) # This route requires a valid refresh token
def refresh_and_retry():
    """
    This endpoint is designed to be called automatically for web clients 
    when an access token expires. The `expired_token_loader` in `__init__.py`
    redirects the original failed request here.
    
    It generates a new access token and then redirects the user back to their
    original intended URL, with the new token set in a cookie.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    
    # Create a new non-fresh access token.
    # We can add the same claims as in the original login.
    additional_claims = {"is_super_user": user.is_super_user if user else False}
    new_access_token = create_access_token(identity=str(current_user_id), fresh=False, additional_claims=additional_claims)
    
    # Get the original URL the user was trying to access
    original_url = request.args.get('original_url', url_for('main_bp.index'))
    
    # Create a redirect response to the original URL
    resp = make_response(redirect(original_url))
    
    # Set the new access token in the cookies
    set_access_cookies(resp, new_access_token)
    
    return resp

# ===================================================================================
# API Routes (Header-based for Mobile/SPA)
# ===================================================================================

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """
    Handles the login process for API clients (e.g., mobile apps).
    Expects email and password in a JSON payload.
    Returns JWT access and refresh tokens in the JSON response body.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON in request"}), 400

    email = data.get('email', None)
    password = data.get('password', None)
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        # Create tokens
        additional_claims = {"is_super_user": user.is_super_user}
        access_token = create_access_token(identity=str(user.id), fresh=True, additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True) # Requires a valid refresh token in the 'Authorization' header
def api_refresh():
    """
    Handles token refreshing for API clients.
    The client sends its valid refresh token in the Authorization header,
    and this endpoint returns a new, non-fresh access token.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get((current_user_id))
    
    # Create a new access token with the same claims
    additional_claims = {"is_super_user": user.is_super_user if user else False}
    new_access_token = create_access_token(identity=str(current_user_id), fresh=False, additional_claims=additional_claims)
    
    return jsonify(access_token=new_access_token), 200

@auth_bp.route('/api/logout', methods=['POST'])
@jwt_required()
def api_logout():
    """
    For API clients, true server-side logout is complex and often handled
    by token blocklisting. A simpler, stateless approach is for the client
    to simply discard its tokens upon calling this endpoint.
    This endpoint serves as a confirmation of that action.
    """
    # For blocklisting, you would add the token's jti (JWT ID) to a blocklist here.
    # jti = get_jwt()['jti']
    # blocklist.add(jti)
    return jsonify({"message": "Logout successful. Please discard the tokens."}), 200
