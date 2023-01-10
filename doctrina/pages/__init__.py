from .auth import bp as auth_bp
from .channel import bp as channel_bp
from .contexts import context as context_bp
from .errors import bp as error_bp
from .generic import bp as generic_bp
from .profile import bp as profile_bp
from .resource import bp as resource_bp


def register_all_blueprints(app) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(channel_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(generic_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(resource_bp)


def load_context(app) -> None:
    app.register_blueprint(context_bp)
