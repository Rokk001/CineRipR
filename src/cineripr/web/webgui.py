"""WebGUI for CineRipR status monitoring - Legacy compatibility wrapper."""

from __future__ import annotations

import logging

from .app import create_app

_LOGGER = logging.getLogger(__name__)

# Legacy exports for backward compatibility
# The actual implementation is now in app.py and routes/

def run_webgui(host: str = "0.0.0.0", port: int = 8080, debug: bool = False) -> None:
    """Run the WebGUI server."""
    try:
        app = create_app()
        _LOGGER.info(f"Starting WebGUI on http://{host}:{port}")
        app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
    except OSError as exc:
        _LOGGER.error(f"Failed to start WebGUI: {exc}")
        raise
