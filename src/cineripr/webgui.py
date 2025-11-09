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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e9ecef;
            min-height: 100vh;
            padding: 20px;
            overflow-x: hidden;
        }
        
        /* Animated Background Particles */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0.3;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            animation: float 20s infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); }
            25% { transform: translateY(-100px) translateX(50px); }
            50% { transform: translateY(-50px) translateX(-50px); }
            75% { transform: translateY(-150px) translateX(100px); }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        /* Glassmorphism Header */
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideDown 0.6s ease-out;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .header-icon {
            font-size: 4em;
            margin-bottom: 15px;
            display: inline-block;
            animation: rotate3d 3s ease-in-out infinite;
        }
        
        @keyframes rotate3d {
            0%, 100% { transform: rotateY(0deg); }
            50% { transform: rotateY(180deg); }
        }
        
        .header h1 {
            font-size: 3em;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.2em;
            font-weight: 400;
        }
        
        .content {
            animation: fadeIn 0.8s ease-out 0.2s both;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Stats Grid */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: scaleIn 0.5s ease-out backwards;
        }
        
        .stat-card:nth-child(1) { animation-delay: 0.1s; }
        .stat-card:nth-child(2) { animation-delay: 0.2s; }
        .stat-card:nth-child(3) { animation-delay: 0.3s; }
        .stat-card:nth-child(4) { animation-delay: 0.4s; }
        
        @keyframes scaleIn {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .stat-card:hover::before {
            opacity: 1;
        }
        
        .stat-card.success { --accent-color: #10b981; }
        .stat-card.error { --accent-color: #ef4444; }
        .stat-card.warning { --accent-color: #f59e0b; }
        .stat-card.info { --accent-color: #3b82f6; }
        
        .stat-card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            background: linear-gradient(135deg, var(--accent-color), transparent);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }
        
        .stat-card h3 {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .stat-card .value {
            font-size: 3em;
            font-weight: 700;
            color: var(--accent-color);
            text-shadow: 0 0 20px rgba(var(--accent-color), 0.5);
            transition: all 0.3s;
        }
        
        .stat-card:hover .value {
            transform: scale(1.1);
        }
        
        /* Current Operation Section */
        .current-operation {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            animation: fadeIn 0.8s ease-out 0.4s both;
        }
        
        .current-operation h2 {
            margin-bottom: 20px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.5em;
        }
        
        .status-indicator {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            position: relative;
        }
        
        .status-indicator.running {
            background: #10b981;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
            animation: pulse 2s infinite;
        }
        
        .status-indicator.running::after {
            content: '';
            position: absolute;
            top: -4px;
            left: -4px;
            right: -4px;
            bottom: -4px;
            border-radius: 50%;
            border: 2px solid #10b981;
            animation: ripple 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.1); }
        }
        
        @keyframes ripple {
            0% { transform: scale(1); opacity: 1; }
            100% { transform: scale(1.5); opacity: 0; }
        }
        
        .status-indicator.idle {
            background: #6b7280;
            box-shadow: 0 0 10px rgba(107, 114, 128, 0.4);
        }
        
        .release-info {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 15px;
            margin-bottom: 20px;
            font-size: 1.05em;
        }
        
        .release-info strong {
            color: rgba(255, 255, 255, 0.6);
            min-width: 150px;
        }
        
        .release-info span {
            color: #fff;
            word-break: break-all;
        }
        
        /* Progress Bar */
        .progress-container {
            margin: 20px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 40px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            overflow: hidden;
            position: relative;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 200% 100%;
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 1em;
            position: relative;
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            animation: slide 2s infinite;
        }
        
        @keyframes slide {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .status-message {
            margin-top: 15px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 1em;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            border-left: 3px solid #667eea;
        }
        
        /* Logs Section */
        .logs {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 0.9em;
            line-height: 1.6;
        }
        
        .logs::-webkit-scrollbar {
            width: 8px;
        }
        
        .logs::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }
        
        .logs::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        
        .logs::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .log-entry {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-left: 3px solid transparent;
            border-radius: 4px;
            background: rgba(0, 0, 0, 0.2);
            transition: all 0.2s;
            animation: slideInLeft 0.3s ease-out;
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .log-entry:hover {
            background: rgba(0, 0, 0, 0.4);
            border-left-width: 4px;
        }
        
        .log-entry.info { border-left-color: #3b82f6; }
        .log-entry.warning { border-left-color: #f59e0b; }
        .log-entry.error { border-left-color: #ef4444; }
        .log-entry.debug { border-left-color: #6b7280; }
        
        /* Footer */
        .refresh-info {
            text-align: center;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 30px;
            font-size: 0.95em;
            padding: 20px;
            animation: fadeIn 1s ease-out 0.6s both;
        }
        
        .refresh-info .pulse {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .status-grid {
                grid-template-columns: 1fr;
            }
            
            .stat-card .value {
                font-size: 2.5em;
            }
            
            .release-info {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .release-info strong {
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <!-- Animated Background -->
    <div class="particles" id="particles"></div>
    
    <div class="container">
        <div class="header">
            <div class="header-icon">🎬</div>
            <h1>CineRipR</h1>
            <div class="subtitle">Archive Extraction & Processing Status</div>
        </div>
        
        <div class="content">
            <div class="status-grid">
                <div class="stat-card success">
                    <div class="stat-card-header">
                        <div class="stat-icon">✓</div>
                        <h3>Verarbeitet</h3>
                    </div>
                    <div class="value" id="processed">0</div>
                </div>
                <div class="stat-card error">
                    <div class="stat-card-header">
                        <div class="stat-icon">✗</div>
                        <h3>Fehlgeschlagen</h3>
                    </div>
                    <div class="value" id="failed">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-card-header">
                        <div class="stat-icon">⚠</div>
                        <h3>Nicht unterstützt</h3>
                    </div>
                    <div class="value" id="unsupported">0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-card-header">
                        <div class="stat-icon">🗑</div>
                        <h3>Gelöscht</h3>
                    </div>
                    <div class="value" id="deleted">0</div>
                </div>
            </div>
            
            <div class="current-operation">
                <h2>
                    <span class="status-indicator" id="status-indicator"></span>
                    Status: <span id="status-text">Idle</span>
                </h2>
                <div id="current-release">
                    <div class="release-info">
                        <strong>Aktuelles Release:</strong>
                        <span id="release-name">-</span>
                    </div>
                    <div class="release-info">
                        <strong>Archiv:</strong>
                        <span id="archive-name">-</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill" style="width: 0%">0%</div>
                        </div>
                    </div>
                    <div class="status-message" id="status-message">-</div>
                </div>
            </div>
            
            <div class="current-operation">
                <h2>📋 Logs</h2>
                <div class="logs" id="logs"></div>
            </div>
            
            <div class="refresh-info">
                <span class="pulse"></span>
                Letzte Aktualisierung: <span id="last-update">-</span> | Auto-Refresh alle 2 Sekunden
            </div>
        </div>
    </div>
    
    <script>
        // Create animated background particles
        function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 20 + 's';
                container.appendChild(particle);
            }
        }
        
        createParticles();
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update counts with animation
                    updateValueWithAnimation('processed', data.processed_count || 0);
                    updateValueWithAnimation('failed', data.failed_count || 0);
                    updateValueWithAnimation('unsupported', data.unsupported_count || 0);
                    updateValueWithAnimation('deleted', data.deleted_count || 0);
                    
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
                    const currentScroll = logsContainer.scrollTop;
                    const isScrolledToBottom = logsContainer.scrollHeight - logsContainer.clientHeight <= currentScroll + 10;
                    
                    logsContainer.innerHTML = '';
                    if (data.recent_logs && data.recent_logs.length > 0) {
                        data.recent_logs.slice().reverse().forEach(log => {
                            const logEntry = document.createElement('div');
                            logEntry.className = 'log-entry ' + (log.level || 'info').toLowerCase();
                            const time = new Date(log.timestamp).toLocaleTimeString('de-DE');
                            logEntry.textContent = `[${time}] [${log.level || 'INFO'}] ${log.message || ''}`;
                            logsContainer.appendChild(logEntry);
                        });
                        
                        // Auto-scroll to bottom if was already at bottom
                        if (isScrolledToBottom) {
                            logsContainer.scrollTop = logsContainer.scrollHeight;
                        }
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
        
        function updateValueWithAnimation(elementId, newValue) {
            const element = document.getElementById(elementId);
            const currentValue = parseInt(element.textContent) || 0;
            
            if (currentValue !== newValue) {
                element.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    element.textContent = newValue;
                    element.style.transform = 'scale(1)';
                }, 150);
            }
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


