# app/admin/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, DecimalField, SelectMultipleField
from wtforms.validators import DataRequired, URL, Optional, Regexp, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.widgets import CheckboxInput

# A master list of all possible facilities. This makes it easy to add more later.
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

class AddHotelForm(FlaskForm):
    name = StringField('Hotel Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    # We use a custom regex here to ensure the coordinate format is correct
    coordinates = StringField('Coordinates (Lon, Lat)', validators=[
        DataRequired(),
        Regexp(r'^-?\d+\.\d+,\s*-?\d+\.\d+$', message="Invalid format. Must be 'longitude, latitude' e.g., -0.1410, 50.8225")
    ])
    website = StringField('Website', validators=[DataRequired(), URL()])
    phone = StringField('Phone Number', validators=[Optional()])
    is_featured = BooleanField('Mark as Featured')
    status = SelectField('Status', choices=[('approved', 'Approved'), ('pending', 'Pending'), ('offline', 'Offline')], validators=[DataRequired()])

    # --- NEW FIELDS FOR FILTERING ---
    accommodation_type = SelectField(
        'Accommodation Type',
        choices=[
            ('Hotel', 'Hotel'),
            ('B&B', 'B&B'),
            ('Pub with Rooms', 'Pub with Rooms'),
            ('Hostel', 'Hostel'),
            ('Guesthouse', 'Guesthouse'),
            ('Other', 'Other'),
            ('Camping', 'Camping')
        ],
        validators=[Optional()]
    )
    star_rating = SelectField(
        'Star Rating',
        choices=[(str(i), f'{i} Stars') for i in range(1, 6)],
        coerce=str,
        validators=[Optional()]
    )
    price_range = SelectField(
        'Price Range',
        choices=[
            ('£', '£ (Budget)'),
            ('££', '££ (Mid-range)'),
            ('£££', '£££ (Premium)'),
            ('££££', '££££ (Exclusive)')
        ],
        validators=[Optional()]
    )
    google_rating = DecimalField(
        'Google Rating (e.g., 4.5)',
        places=1,
        validators=[Optional(), NumberRange(min=1, max=5)]
    )
    # This renders our FACILITIES_CHOICES list as a series of checkboxes
    facilities = SelectMultipleField(
        'Facilities',
        choices=FACILITIES_CHOICES,
        widget=CheckboxInput(),
        coerce=str
    )

    submit = SubmitField('Submit')


class AddRouteForm(FlaskForm):
    name = StringField('Route Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    surface_type = SelectField('Surface Type', choices=[('Road', 'Road'), ('Gravel', 'Gravel'), ('Mixed', 'Mixed')], validators=[DataRequired()])
    gpx_file = FileField('GPX File', validators=[FileRequired(), FileAllowed(['gpx'], 'GPX files only!')])
    submit = SubmitField('Add Route')


class EditRouteForm(FlaskForm):
    name = StringField('Route Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    surface_type = SelectField('Surface Type', choices=[('Road', 'Road'), ('Gravel', 'Gravel'), ('Mixed', 'Mixed')], validators=[DataRequired()])
    # The GPX file is now optional when editing
    gpx_file = FileField('Upload New GPX File (Optional)', validators=[FileAllowed(['gpx'], 'GPX files only!')])
    submit = SubmitField('Save Changes')
