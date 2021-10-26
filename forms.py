############################################################################
# Configuration of flask forms for the application.
#
#
# works of OfficialTeamName (con'd). All rights reserved.
###########################################################################
from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, TextAreaField, FileField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """Form class for user login."""
    email = TextField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    """Form class for user register."""
    username = TextField('username', validators=[DataRequired()])
    email = TextField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    passwordConfirm = PasswordField('passwordConfirm', validators=[DataRequired()])


class ResourceForm(FlaskForm):
    """Form class for user new resource."""
    title =TextAreaField('title', validators=[DataRequired()])
    description =TextAreaField('description', validators=[DataRequired()])
    files = FileField('File')
    resource_url = TextAreaField("resource_url")
    thumbnail = FileField('File', validators=[DataRequired()])
