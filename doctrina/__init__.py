import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_redis import FlaskRedis
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from .config import Config

# perform generic inits
db = SQLAlchemy()
db_session = db.session

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "You need to be logged in to view this page"
login_manager.login_message_category = "error"

redis_client = FlaskRedis()

# Not to be used, instead use flask.session, used for cookies in flask_login
server_session = Session()

bootstrap = Bootstrap5()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    redis_client.init_app(app)
    # set session redis to be newly created redis client
    app.config["SESSION_REDIS"] = redis_client._redis_client

    server_session.init_app(app)
    bootstrap.init_app(app)

    # configure logging
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s")
    )
    app.logger.addHandler(stream_handler)
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/doctinra.log", maxBytes=10240, backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"))
    app.logger.addHandler(file_handler)

    with app.app_context():
        # load all Blueprints and context
        from doctrina.pages import load_context, register_all_blueprints

        load_context(app)
        register_all_blueprints(app)

        # Create DB
        db.create_all()

    return app


from .database import models
