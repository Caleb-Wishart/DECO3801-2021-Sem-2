from flask import Blueprint

bp = Blueprint("resource", __name__)

from . import api, routes
