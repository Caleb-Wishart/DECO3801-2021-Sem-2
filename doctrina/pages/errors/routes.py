from flask import current_app, render_template
from werkzeug.exceptions import HTTPException, InternalServerError, NotFound

from . import bp


@bp.app_errorhandler(NotFound)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(InternalServerError)
def internal_error(error):
    return render_template("errors/500.html"), 500


@bp.app_errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        title = f"{e.code} - {e.name}"
        return render_template("errors/error_generic.html", e=e, title=title), e.code

    # non-HTTP exceptions default to 500
    if current_app.config.get("DEBUG", False):
        current_app.logger.warn(str(e))
        return render_template("errors/error_generic.html", e=InternalServerError(), fail=str(e)), 500
    return render_template("errors/error_generic.html", e=InternalServerError()), 500
