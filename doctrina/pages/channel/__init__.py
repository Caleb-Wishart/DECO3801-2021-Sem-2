from flask import Blueprint

bp = Blueprint("channel", __name__)

from . import api, routes
