from datetime import datetime

from flask import Blueprint
from flask_login import current_user

from doctrina.database.database import enum_to_website_output, get_tags
from doctrina.database.models import Grade, Subject

context = Blueprint("context", __name__)


@context.app_context_processor
def inject_now():
    return {"now": datetime.utcnow()}


@context.app_context_processor
def subject_processor():
    return dict(enum_to_website_output=enum_to_website_output)


@context.app_context_processor
def defaults():
    """Provides the default context processors

    Returns:
        dict: Variables for JINJA context
            current_user: the user the is currently logged in or the Anonymous user
            subject : A list of all subjects with their names
            grade : A list of all grades with their names
            tag : A list of all tags with their names
    """
    return dict(
        current_user=current_user,
        subjects=[e.name.lower() for e in Subject if e.name != "NULL"],
        grades=[e.name.lower() for e in Grade if e.name != "NULL"],
        tags=[e.replace(" ", "_") for e in get_tags().keys()],
    )
