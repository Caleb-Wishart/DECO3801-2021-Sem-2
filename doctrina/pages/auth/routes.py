from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from doctrina import db_session
from doctrina.database.database import ErrorCode, add_user, get_user, user_auth
from doctrina.database.models import DemoUser, User

from . import bp
from .forms import LoginForm, RegisterForm

current_user: User


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page for a user to authenticate
    Asks for the users email and password.
    Gives feedback on fail, redirects to referring page on success
            (through GET data), if not refered then home page
    """
    if current_user.is_authenticated:
        return redirect(url_for("base.home"))

    form = LoginForm()
    if form.validate_on_submit():
        if form.register.data:
            return redirect(url_for("auth.register"))
        email = form.email.data
        password = form.password.data
        if current_app.config.get("DEMO_MODE", False):
            if email == "demo" and password == "demo":
                login_user(DemoUser(), remember=False)
                if "next" in request.args and request.args.get("next") != url_for("auth.logout"):
                    return redirect(request.args.get("next", url_for("home")))
                return redirect(url_for("home"))

        user = get_user(email)
        if user is None or not user.check_password(password):
            flash("That username or password was incorrect", "error")
            return redirect(url_for("auth.login"))
        user_auth(user, login=True)
        login_user(user, remember=False)
        next_page = request.args.get("next")
        if not next_page or next_page == url_for("auth.logout"):
            next_page = url_for("base.home")
        return redirect(next_page)
    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/logout")
def logout():
    user_auth(current_user, login=False)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("base.home"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Page for a user to register for an account

    Must provide: username, email, password (with conditions)

    Optionally provide: interests / subjects tags

    Other user fields are configured in profile()
    """
    if current_user.is_authenticated:
        return redirect(url_for("base.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        with db_session():
            # add user and log in
            res = add_user(form.username.data, form.password.data, form.email.data)

            if res == ErrorCode.COMMIT_ERROR:
                flash("Something went wrong, please try again", "error")
                return redirect(url_for("auth.register"))

            flash("Thank you for registering!")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title="Register", form=form)
