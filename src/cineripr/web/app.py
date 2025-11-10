"""Flask application factory."""

import logging
from flask import Flask
from .routes import register_blueprints
from .services.status_tracker import get_status_tracker
from .settings_db import get_settings_db

_logger = logging.getLogger(__name__)

def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    
    # Initialize tracker with DB settings
    tracker = get_status_tracker()
    try:
        db = get_settings_db()
        db_settings = db.get_all()
        repeat_forever = db_settings.get("repeat_forever", True)  # Default: True
        repeat_after_minutes = db_settings.get("repeat_after_minutes", 30)  # Default: 30
        
        tracker.set_repeat_mode(bool(repeat_forever), interval_minutes=int(repeat_after_minutes))
        
        if repeat_forever and repeat_after_minutes > 0:
            tracker.set_next_run(int(repeat_after_minutes))
    except Exception as e:
        _logger.debug(f"Failed to initialize tracker with DB settings in create_app: {e}")
    
    # Register blueprints
    register_blueprints(app, tracker)
    
    return app

