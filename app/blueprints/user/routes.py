# app/user/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.blueprints.user.forms import CreateUserForm, InitiateResetPasswordForm, ResetPasswordForm, EditAccountForm
from app.models.password_reset_token import generate_password_reset_token
from app.decorators import admin_required
from datetime import datetime, timezone

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data)
        user.set_password('temporary_password')  # Set a temporary password
        for role in form.roles.data:
            user.add_role(role)
        db.session.add(user)
        db.session.commit()

        # Generate password reset token
        reset_token, expiration = generate_password_reset_token(user)
        
        # Generate the reset link
        reset_link = url_for('user_bp.reset_password', token=reset_token.token, _external=True)

        flash('New user created successfully. Please send the following link to the user to set their password:', 'success')
        return render_template('user/create_user_verification.html', reset_link=reset_link)
    
    return render_template('user/create_user.html', title='Create User', form=form)

@user_bp.route('/initiate_reset_password', methods=['GET', 'POST'])
@login_required
@admin_required
def initiate_reset_password():
    form = InitiateResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            reset_token, expiration = generate_password_reset_token(user)
            reset_link = url_for('user_bp.reset_password', token=reset_token.token, _external=True)
            flash('Password reset link generated. Please send the following link to the user:', 'success')
            return render_template('user/reset_password_link.html', reset_link=reset_link)
    return render_template('user/initiate_reset_password.html', title='Initiate Password Reset', form=form)

@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth_bp.login'))

    user = User.query.get(reset_token.user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth_bp.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        reset_token.used = True
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth_bp.login'))

    return render_template('user/reset_password.html', form=form)

@user_bp.route('/edit_account', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditAccountForm()
    if form.validate_on_submit():
        if form.email.data and form.email.data != current_user.email:
            current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your account has been updated.', 'success')
        return redirect(url_for('user_bp.edit_account'))
    elif request.method == 'GET':
        form.email.data = current_user.email
    return render_template('user/edit_account.html', title='Edit Account', form=form)
