# app/blog/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

class PostForm(FlaskForm):
    """Form for admin to create or edit a blog post."""
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=120)])
    # A simple textarea for the content. For a real app, you might use a rich text editor.
    content = TextAreaField('Content', validators=[DataRequired()])
    status = SelectField('Status', choices=[('draft', 'Draft'), ('published', 'Published')],
                         validators=[DataRequired()])
    submit = SubmitField('Save Post')
