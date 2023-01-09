from flask import Blueprint

bp = Blueprint("generic", __name__)

from . import api, routes
