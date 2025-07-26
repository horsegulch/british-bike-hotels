# app/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """
    Defines the fields and validation rules for the admin login form.
    
    Each attribute of the class represents a form field. The type of field
    (e.g., StringField, PasswordField) determines its HTML rendering and
    basic data type.
    
    The `validators` argument is a list of objects that check the submitted
    data for correctness.
    """
    
    # Username field: A text input.
    # Validators:
    # - DataRequired: Ensures the field is not submitted empty.
    # - Length: Ensures the username is between 4 and 25 characters.
    username = StringField(
        'Username', 
        validators=[DataRequired(), Length(min=4, max=25)]
    )

    # Password field: A password input that masks the text.
    # Validators:
    # - DataRequired: Ensures the password is not submitted empty.
    password = PasswordField(
        'Password', 
        validators=[DataRequired()]
    )

    # Remember me checkbox (optional feature for later)
    remember_me = BooleanField('Remember Me')

    # Submit button for the form.
    submit = SubmitField('Log In')
