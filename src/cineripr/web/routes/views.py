"""View routes (HTML pages)."""

from flask import Blueprint, render_template, send_from_directory
from pathlib import Path
from ... import __version__

# Favicon SVG (embedded)
FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="20" fill="url(#grad1)"/>
  <text x="50" y="70" font-size="60" text-anchor="middle" fill="white">🎬</text>
</svg>'''

views_bp = Blueprint('views', __name__)

@views_bp.route("/")
def index():
    """Serve main dashboard."""
    return render_template('index.html', version=__version__)

@views_bp.route("/favicon.svg")
def favicon():
    """Serve favicon."""
    static_dir = Path(__file__).parent.parent / 'static'
    return send_from_directory(str(static_dir), 'favicon.svg', mimetype='image/svg+xml')

