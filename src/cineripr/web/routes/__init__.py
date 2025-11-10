"""Route blueprints registration."""

from flask import Flask
from .views import views_bp
from .api import api_bp
from .settings import settings_bp

def register_blueprints(app: Flask, tracker) -> None:
    """Register all blueprints."""
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)

