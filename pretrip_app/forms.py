from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class NewTemplateForm(FlaskForm):
    """Form for creating a new PretripTemplate."""
    name = StringField(
        'Template Name',
        validators=[
            DataRequired(message="Template name is required."),
            Length(min=3, max=255)
        ],
        render_kw={"placeholder": "e.g., Class A Tractor Daily Inspection"}
    )
    description = TextAreaField(
        'Description',
        validators=[Length(max=1000)],
        render_kw={"placeholder": "A brief description of what this template is for.", "rows": 3}
    )
    equipment_type = StringField(
        'Equipment Type',
        validators=[Length(max=255)],
        render_kw={"placeholder": "e.g., Tractor, Trailer, Forklift"}
    )
    submit = SubmitField('Create Template')


class NewItemForm(FlaskForm):
    """Form for creating a new PretripItem and adding it to a template."""
    text = StringField(
        'Item Text',
        validators=[
            DataRequired(message="Item text cannot be empty."),
            Length(min=5, max=255)
        ],
        render_kw={"placeholder": "e.g., Check engine oil level"}
    )
    submit = SubmitField('Add Item')
