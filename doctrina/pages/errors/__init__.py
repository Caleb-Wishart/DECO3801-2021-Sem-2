from flask import Blueprint

bp = Blueprint("error", __name__)

from . import routes
