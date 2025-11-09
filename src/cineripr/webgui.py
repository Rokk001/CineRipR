"""WebGUI for CineRipR status monitoring."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, render_template_string

from .status import get_status_tracker

_LOGGER = logging.getLogger(__name__)

# HTML Template for the WebGUI
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CineRipR - Status Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header .subtitle {
            opacity: 0.9;
            font-size: 1.1em;
        }
        .content {
            padding: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        .stat-card h3 {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .stat-card.success { border-left-color: #28a745; }
        .stat-card.warning { border-left-color: #ffc107; }
        .stat-card.error { border-left-color: #dc3545; }
        .current-operation {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .current-operation h2 {
            margin-bottom: 15px;
            color: #333;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }
        .logs {
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 8px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .log-entry {
            margin-bottom: 8px;
            padding: 5px;
            border-left: 3px solid transparent;
        }
        .log-entry.info { border-left-color: #17a2b8; }
        .log-entry.warning { border-left-color: #ffc107; }
        .log-entry.error { border-left-color: #dc3545; }
        .log-entry.debug { border-left-color: #6c757d; }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-indicator.running {
            background: #28a745;
            animation: pulse 2s infinite;
        }
        .status-indicator.idle {
            background: #6c757d;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .refresh-info {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 CineRipR</h1>
            <div class="subtitle">Archive Extraction & Processing Status</div>
        </div>
        <div class="content">
            <div class="status-grid">
                <div class="stat-card success">
                    <h3>Verarbeitet</h3>
                    <div class="value" id="processed">0</div>
                </div>
                <div class="stat-card error">
                    <h3>Fehlgeschlagen</h3>
                    <div class="value" id="failed">0</div>
                </div>
                <div class="stat-card warning">
                    <h3>Nicht unterstützt</h3>
                    <div class="value" id="unsupported">0</div>
                </div>
                <div class="stat-card success">
                    <h3>Gelöscht</h3>
                    <div class="value" id="deleted">0</div>
                </div>
            </div>
            
            <div class="current-operation">
                <h2>
                    <span class="status-indicator" id="status-indicator"></span>
                    Status: <span id="status-text">Idle</span>
                </h2>
                <div id="current-release">
                    <p><strong>Aktuelles Release:</strong> <span id="release-name">-</span></p>
                    <p><strong>Archiv:</strong> <span id="archive-name">-</span></p>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%">0%</div>
                    </div>
                    <p id="status-message" style="margin-top: 10px; color: #666;">-</p>
                </div>
            </div>
            
            <div class="current-operation">
                <h2>Logs</h2>
                <div class="logs" id="logs"></div>
            </div>
            
            <div class="refresh-info">
                Letzte Aktualisierung: <span id="last-update">-</span> | Auto-Refresh alle 2 Sekunden
            </div>
        </div>
    </div>
    
    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update counts
                    document.getElementById('processed').textContent = data.processed_count || 0;
                    document.getElementById('failed').textContent = data.failed_count || 0;
                    document.getElementById('unsupported').textContent = data.unsupported_count || 0;
                    document.getElementById('deleted').textContent = data.deleted_count || 0;
                    
                    // Update status
                    const isRunning = data.is_running || false;
                    const statusIndicator = document.getElementById('status-indicator');
                    const statusText = document.getElementById('status-text');
                    
                    if (isRunning) {
                        statusIndicator.className = 'status-indicator running';
                        statusText.textContent = 'Läuft';
                    } else {
                        statusIndicator.className = 'status-indicator idle';
                        statusText.textContent = 'Idle';
                    }
                    
                    // Update current release
                    const currentRelease = data.current_release;
                    if (currentRelease) {
                        document.getElementById('release-name').textContent = currentRelease.release_name || '-';
                        document.getElementById('archive-name').textContent = currentRelease.current_archive || '-';
                        
                        const progress = currentRelease.archive_total > 0 
                            ? Math.round((currentRelease.archive_progress / currentRelease.archive_total) * 100)
                            : 0;
                        const progressFill = document.getElementById('progress-fill');
                        progressFill.style.width = progress + '%';
                        progressFill.textContent = progress + '%';
                        
                        document.getElementById('status-message').textContent = currentRelease.message || '-';
                    } else {
                        document.getElementById('release-name').textContent = '-';
                        document.getElementById('archive-name').textContent = '-';
                        document.getElementById('progress-fill').style.width = '0%';
                        document.getElementById('progress-fill').textContent = '0%';
                        document.getElementById('status-message').textContent = '-';
                    }
                    
                    // Update logs
                    const logsContainer = document.getElementById('logs');
                    logsContainer.innerHTML = '';
                    if (data.recent_logs && data.recent_logs.length > 0) {
                        data.recent_logs.slice().reverse().forEach(log => {
                            const logEntry = document.createElement('div');
                            logEntry.className = 'log-entry ' + (log.level || 'info').toLowerCase();
                            const time = new Date(log.timestamp).toLocaleTimeString('de-DE');
                            logEntry.textContent = `[${time}] [${log.level || 'INFO'}] ${log.message || ''}`;
                            logsContainer.appendChild(logEntry);
                        });
                    }
                    
                    // Update last update time
                    if (data.last_update) {
                        const updateTime = new Date(data.last_update);
                        document.getElementById('last-update').textContent = updateTime.toLocaleString('de-DE');
                    }
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                });
        }
        
        // Initial load
        updateStatus();
        
        // Auto-refresh every 2 seconds
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>"""


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    # Suppress Flask's default logging to avoid noise
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    tracker = get_status_tracker()

    @app.route("/")
    def index() -> str:
        """Serve the main dashboard page."""
        return render_template_string(HTML_TEMPLATE)

    @app.route("/api/status")
    def api_status() -> Any:
        """Get current status as JSON."""
        status = tracker.get_status()
        return jsonify(status.to_dict())

    @app.route("/api/health")
    def api_health() -> Any:
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "cineripr-webgui"})

    return app


def run_webgui(host: str = "0.0.0.0", port: int = 8080, debug: bool = False) -> None:
    """Run the WebGUI server."""
    try:
        app = create_app()
        _LOGGER.info(f"Starting WebGUI on http://{host}:{port}")
        # Flask's run() is blocking, so this will keep running
        app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
    except OSError as exc:
        if "Address already in use" in str(exc) or "address is already in use" in str(exc):
            _LOGGER.error(f"Port {port} is already in use. Try a different port with --webgui-port")
        else:
            _LOGGER.error(f"Failed to start WebGUI: {exc}", exc_info=True)
        raise
    except Exception as exc:
        _LOGGER.error(f"Failed to start WebGUI: {exc}", exc_info=True)
        raise


__all__ = ["create_app", "run_webgui"]

