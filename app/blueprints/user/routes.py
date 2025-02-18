# app/user/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.blueprints.user.forms import CreateUserForm, InitiateResetPasswordForm, ResetPasswordForm, EditAccountForm
from app.models.password_reset_token import generate_password_reset_token
from app.decorators import admin_required
from werkzeug.exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        try:
            # Create new user
            user = User(email=form.email.data, username=form.username.data)
            user.set_password('temporary_password')

            logger.info(f"Creating new user: email={form.email.data}, username={form.username.data}")
            
            try:
                db.session.add(user)
                db.session.commit()
                logger.info(f"Successfully created user with ID: {user.id}")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error while creating user: {str(e)}")
                raise InternalServerError("Database error occurred")

            try:
                # Generate password reset token
                reset_token, expiration = generate_password_reset_token(user)
                
                # Generate the reset link
                reset_link = url_for('user_bp.reset_password', 
                                   token=reset_token.token, 
                                   _external=True,
                                   _=None) # underscore parameter dictates no trailing slash in the created link.

                flash('New user created successfully. Please send the following link to the user to set their password:', 'success')
                return render_template('user/create_user_verification.html', 
                                    reset_link=reset_link)

            except Exception as e:
                logger.error(f"Error generating password reset token: {str(e)}")
                # Note: User is already created, so we don't rollback
                flash('User created but there was an error generating the password reset link.', 'warning')
                return render_template('user/create_user.html', 
                                    title='Create User', 
                                    form=form), 500

        except Exception as e:
            logger.exception("Unexpected error in user creation process")
            raise InternalServerError("An unexpected error occurred")

    # Log form validation errors
    if form.errors:
        logger.warning(f"Form validation failed with errors: {form.errors}")
        
    return render_template('user/create_user.html', title='Create User', form=form)

@user_bp.route('/initiate_reset_password', methods=['GET', 'POST'])
@login_required
@admin_required
def initiate_reset_password():
    form = InitiateResetPasswordForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                try:
                    reset_token, expiration = generate_password_reset_token(user)
                    reset_link = url_for('user_bp.reset_password', 
                                       token=reset_token.token, 
                                       _external=True, 
                                       _=None)
                    
                    logger.info(f"Successfully generated password reset token user: email={form.email.data}")
                    flash('Password reset link generated. Please send the following link to the user:', 'success')
                    return render_template('user/reset_password_link.html', reset_link=reset_link)
                
                except Exception as e:
                    logger.error(f"Error generating password reset token: {str(e)}")
                    flash('An error occurred while generating the password reset link.', 'danger')
                    return render_template('user/initiate_reset_password.html', 
                                        title='Initiate Password Reset', 
                                        form=form), 500
            else:
                logger.warning(f"Password reset attempted for non-existent email: {form.email.data}")
                # Note: We still show the same message to avoid user enumeration
                flash('Password reset attempted for non-existent email.', 'info')

        except Exception as e:
            logger.exception("Unexpected error in password reset initiation process")
            raise InternalServerError("An unexpected error occurred")

    # Log form validation errors
    if form.errors:
        logger.warning(f"Form validation failed with errors: {form.errors}")

    return render_template('user/initiate_reset_password.html', title='Initiate Password Reset', form=form)

@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
        if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Invalid or expired password reset attempt with token: {token}")
            flash('The password reset link is invalid or has expired.', 'danger')
            return redirect(url_for('auth_bp.login'))

        user = User.query.get(reset_token.user_id)
        if not user:
            logger.error(f"User not found for valid reset token. Token ID: {reset_token.id}, User ID: {reset_token.user_id}")
            flash('User not found.', 'danger')
            return redirect(url_for('auth_bp.login'))

        form = ResetPasswordForm()
        if form.validate_on_submit():
            try:
                user.set_password(form.password.data)
                reset_token.used = True
                
                try:
                    db.session.commit()
                    logger.info(f"Successfully reset password for user ID: {user.id}")
                    flash('Your password has been reset.', 'success')
                    return redirect(url_for('auth_bp.login'))
                
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Database error while resetting password: {str(e)}")
                    flash('An error occurred while resetting your password.', 'danger')
                    return render_template('user/reset_password.html', form=form), 500
                    
            except Exception as e:
                logger.error(f"Error while setting new password: {str(e)}")
                flash('An error occurred while resetting your password.', 'danger')
                return render_template('user/reset_password.html', form=form), 500

        # Log form validation errors
        if form.errors:
            logger.warning(f"Password reset form validation failed with errors: {form.errors}")

        return render_template('user/reset_password.html', form=form)

    except Exception as e:
        logger.exception("Unexpected error in password reset process")
        raise InternalServerError("An unexpected error occurred")

@user_bp.route('/edit_account', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditAccountForm()
    if form.validate_on_submit():
        try:
            if form.email.data and form.email.data != current_user.email:
                current_user.email = form.email.data
            
            if form.password.data:
                current_user.set_password(form.password.data)
            
            try:
                db.session.commit()
                logger.info(f"Successfully updated account for user ID: {current_user.id}")
                flash('Your account has been updated.', 'success')
                return redirect(url_for('user_bp.edit_account'))
            
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error while updating account: {str(e)}")
                flash('An error occurred while updating your account.', 'danger')
                return render_template('user/edit_account.html', 
                                    title='Edit Account', 
                                    form=form), 500
                
        except Exception as e:
            logger.exception("Unexpected error in account update process")
            raise InternalServerError("An unexpected error occurred")

    # Log form validation errors
    if form.errors:
        logger.warning(f"Account edit form validation failed with errors: {form.errors}")

    elif request.method == 'GET':
        form.email.data = current_user.email
        
    return render_template('user/edit_account.html', title='Edit Account', form=form)