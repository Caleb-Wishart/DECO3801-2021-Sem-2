from flask_wtf import FlaskForm
from wtforms import FileField, TextAreaField
from wtforms.validators import DataRequired


class ResourceForm(FlaskForm):
    """Form class for user new resource."""

    title = TextAreaField("title", validators=[DataRequired()])
    description = TextAreaField("description", validators=[DataRequired()])
    files = FileField("File")
    resource_url = TextAreaField("resource_url")
    thumbnail = FileField("File", validators=[DataRequired()])
