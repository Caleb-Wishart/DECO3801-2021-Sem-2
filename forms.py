"""Forms for the application."""
from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField
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
