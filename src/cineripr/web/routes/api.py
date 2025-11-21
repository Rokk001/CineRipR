"""API routes."""

from flask import Blueprint, jsonify, request
from ..services.status_tracker import get_status_tracker
from ..settings_db import get_settings_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/status")
def status():
    """Get current status."""
    tracker = get_status_tracker()
    status = tracker.get_status()
    return jsonify(status.to_dict())

@api_bp.route("/notifications/<notif_id>/read", methods=["POST"])
def mark_notification_read(notif_id: str):
    """Mark a notification as read."""
    tracker = get_status_tracker()
    tracker.mark_notification_read(notif_id)
    return jsonify({"status": "ok"})

@api_bp.route("/theme", methods=["GET", "POST"])
def theme():
    """Get or set theme preference."""
    tracker = get_status_tracker()
    if request.method == "POST":
        data = request.get_json()
        theme = data.get("theme", "dark")
        tracker.set_theme(theme)
        return jsonify({"status": "ok", "theme": theme})
    else:
        return jsonify({"theme": tracker.get_theme()})

@api_bp.route("/control/pause", methods=["POST"])
def pause():
    """Pause processing."""
    tracker = get_status_tracker()
    tracker.pause_processing()
    tracker.add_notification("info", "Processing Paused", "Processing has been paused by user")
    return jsonify({"status": "ok"})

@api_bp.route("/control/resume", methods=["POST"])
def resume():
    """Resume processing."""
    tracker = get_status_tracker()
    tracker.resume_processing()
    tracker.add_notification("info", "Processing Resumed", "Processing has been resumed")
    return jsonify({"status": "ok"})

@api_bp.route("/control/trigger-now", methods=["POST"])
def trigger_now():
    """Skip sleep and trigger next run immediately."""
    tracker = get_status_tracker()
    tracker.trigger_run_now()
    tracker.add_notification("info", "Manual Trigger", "Starting next run immediately...")
    return jsonify({"status": "triggered"})

@api_bp.route("/history")
def history():
    """Get processing history."""
    tracker = get_status_tracker()
    status = tracker.get_status()
    return jsonify(status.to_dict().get("history", []))

@api_bp.route("/queue/preview")
def queue_preview():
    """Get queue preview - what will be processed in next run."""
    try:
        from ...core.archives import _find_release_directories
        from ...config import Settings
        from pathlib import Path
        
        # Get download paths from settings
        db = get_settings_db()
        # For now, return empty list until we can properly access the paths
        # This would require passing settings to the webgui or storing paths in DB
        preview_items = []
        
        return jsonify({"items": preview_items, "count": len(preview_items)})
    except Exception as e:
        return jsonify({"items": [], "count": 0, "error": str(e)})

@api_bp.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "cineripr-webgui"})

@api_bp.route("/system-health", methods=["GET", "POST"])
def system_health():
    """Fetch the latest system health metrics (optionally refreshing first)."""
    tracker = get_status_tracker()
    should_refresh = request.method == "POST" or request.args.get("refresh") == "1"
    if should_refresh:
        tracker.update_system_health()
    status = tracker.get_status()
    system_health = status.to_dict().get("system_health", {})
    return jsonify(system_health)

@api_bp.route("/system/hardware", methods=["GET"])
def system_hardware():
    """Get hardware information."""
    try:
        import psutil

        # Detect disk type (simplified - returns unknown on Windows)
        disk_type = "unknown"
        try:
            # This would need platform-specific logic
            # For now, we'll just return unknown
            disk_type = "SSD"  # TODO: Implement proper detection
        except Exception:
            pass

        return jsonify({
            "cpu_count": psutil.cpu_count(),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
            "disk_type": disk_type,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/setup/wizard", methods=["POST"])
def setup_wizard():
    """Complete setup wizard."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    profile = data.get("profile", "conservative")
    db = get_settings_db()
    tracker = get_status_tracker()

    if profile == "power":
        db.set("parallel_extractions", 2)
        db.set("repeat_after_minutes", 15)
        db.set("finished_retention_days", 14)
        db.set("enable_delete", True)
        db.set("include_other", True)
    # conservative profile uses DEFAULT_SETTINGS

    db.mark_initialized()
    tracker.add_notification("success", "Setup Complete", f"Profile '{profile}' has been applied")

    return jsonify({"status": "completed", "profile": profile})

