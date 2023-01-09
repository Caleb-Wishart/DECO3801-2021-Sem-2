from re import search as re_search

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from doctrina.database.database import ErrorCode, get_user
from doctrina.database.models import User


class LoginForm(FlaskForm):
    """Form class for user login."""

    email = StringField("email", validators=[DataRequired(), Email()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Sign In")
    register = SubmitField("Register")


class RegisterForm(FlaskForm):
    """Form class for user register."""

    username = StringField("username", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired(), Email()])
    password = PasswordField("password", validators=[DataRequired()])
    passwordConfirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = get_user(email.data)
        if user is not None:
            raise ValidationError("Please use a different email address.")

    def validate_password(self, password):
        pwd = password.data
        if len(pwd) < 8:
            raise ValidationError("A password must contain at least 8 letters")
        if re_search("[0-9]", pwd) is None:
            raise ValidationError("A password must contain a number")
        if re_search("[A-Z]", pwd) is None:
            raise ValidationError("A password must contain a capital letter")
