

I am updating a web site to use JWT tokens stored in HTTP only cookies and a CSRF stored in a plain cookie.

Here are some current protected endpoints with forms requiring a custom js post to insert the csrf into the header:

```python
@user_bp.route('/create_user', methods=['GET', 'POST'])
@jwt_required()
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
@jwt_required()
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
    
@user_bp.route('/edit_account', methods=['GET', 'POST'])
@jwt_required()
def edit_account():
    form = EditAccountForm()
    if form.validate_on_submit():
        try:
            if form.email.data and form.email.data != g.current_user.email:
                g.current_user.email = form.email.data
            
            if form.password.data:
                g.current_user.set_password(form.password.data)
            
            try:
                db.session.commit()
                logger.info(f"Successfully updated account for user ID: {g.current_user.id}")
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
        form.email.data = g.current_user.email
        
    return render_template('user/edit_account.html', title='Edit Account', form=form)
    
```
    
Form handler javascript that adds the CSRF when posting (in customFetch), which I would like to update:

```js
document.addEventListener('DOMContentLoaded', () => {
    const protectedForms = document.querySelectorAll('.protected-form');
    protectedForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            customFetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                redirect: 'manual' 
            })
            .then(response => {
                //A successful response means the post succeeded. Reload the page.
                window.location.reload()
            })
            .catch(error => {
                // Catches network errors or the CSRF token not being found.
                console.error('Submission failed:', error);
                alert(`Submission failed: ${error.message}`);
            });
        });
    });
});
```

I would like to coordinate the functionality in the python protected form endpoints and the protected form handling on the client. Right now this code just reloads the page, but I know the server sometimes redirects to a different page.

Before we update any code, I would like you to look at the three endpoints and determina what different cases we need the client code to handle. We can then consider updates to the client and server code.

If you would also like other files, please let me know.