from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    """
    Form for users to log in. This is used for the web-based login form.
    """
    email = StringField('Email', 
                        validators=[
                            DataRequired("Email is required."), 
                            Email("Invalid email format.")
                        ])
    password = PasswordField('Password', 
                             validators=[
                                 DataRequired("Password is required."),
                                 Length(min=8, message="Password must be at least 8 characters long.")
                             ])
    submit = SubmitField('Sign In')
