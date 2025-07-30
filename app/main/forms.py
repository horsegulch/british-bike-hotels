from flask_wtf import FlaskForm
from wtforms import (
    StringField, EmailField, BooleanField, SubmitField, HiddenField, 
    TextAreaField, SelectField, SelectMultipleField, MultipleFileField
)
from wtforms.validators import DataRequired, Email, Length, URL, Optional, Regexp
from flask_wtf.file import FileAllowed

# This is your original form for initial contact
class HotelSignupForm(FlaskForm):
    """Form for hotels to sign up."""
    hotel_name = StringField(
        'Hotel Name', 
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    contact_name = StringField(
        'Your Full Name', 
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = EmailField(
        'Contact Email', 
        validators=[DataRequired(), Email()]
    )
    plan = HiddenField() # This will store 'standard' or 'premium'
    terms_agreed = BooleanField(
        'I have read and agree to the Terms and Conditions', 
        validators=[DataRequired(message="You must agree to the terms to continue.")]
    )
    submit = SubmitField('Complete Sign-up')


# --- NEW ONBOARDING FORM ADDED BELOW ---

# A master list of all possible facilities.
FACILITIES_CHOICES = [
    ('secure_bike_storage', 'Secure Bike Storage'),
    ('bike_wash_station', 'Bike Wash Station'),
    ('workshop_tools', 'Workshop & Tools'),
    ('drying_room', 'Drying Room'),
    ('laundry_service', 'Laundry Service'),
    ('packed_lunches', 'Packed Lunches Available'),
    ('on_site_restaurant', 'On-site Restaurant'),
    ('ev_charging', 'EV Charging')
]

class HotelOnboardingForm(FlaskForm):
    """
    Public-facing form for hotels to submit their full profile details.
    """
    hotel_name = StringField('Hotel Name', validators=[DataRequired(), Length(max=100)])
    coordinates = HiddenField('Coordinates', validators=[
        DataRequired(message="Please select a location on the map."),
        Regexp(r'^-?\d+\.\d+,\s*-?\d+\.\d+$', message="Invalid format. Please select a location on the map.")
    ])
    description = TextAreaField('A short description of your hotel for cyclists', validators=[DataRequired()])
    website = StringField('Website Address', validators=[DataRequired(), URL()])
    phone_number = StringField('Public Phone Number', validators=[DataRequired()])
    
    accommodation_type = SelectField(
        'Accommodation Type', 
        choices=[
            ('Hotel', 'Hotel'), 
            ('B&B', 'B&B'), 
            ('Inn', 'Inn'), 
            ('Guesthouse', 'Guesthouse'),
            ('Other', 'Other')
        ], 
        validators=[DataRequired()]
    )
    
    # This will render as a list of checkboxes for the hotel to select
    facilities = SelectMultipleField(
        'Facilities Available', 
        choices=FACILITIES_CHOICES, 
        coerce=str, 
        validators=[DataRequired(message="Please select at least one facility.")]
    )
    
    # This field allows multiple image uploads
    photos = MultipleFileField(
        'Hotel Photos (up to 5)', 
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
        ]
    )

    # This field allows multiple GPX file uploads
    routes = MultipleFileField(
        'GPX Route Files',
        validators=[
            FileAllowed(['gpx'], 'GPX files only!')
        ]
    )

    submit = SubmitField('Submit for Approval')