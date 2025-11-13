"""Settings routes."""

import logging
from flask import Blueprint, jsonify, request
from ..services.status_tracker import get_status_tracker
from ..settings_db import get_settings_db

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')
_logger = logging.getLogger(__name__)

@settings_bp.route("", methods=["GET"])
def get_all():
    """Get all settings."""
    db = get_settings_db()
    return jsonify(db.get_all())

@settings_bp.route("/<key>", methods=["GET", "POST"])
def item(key: str):
    """Get or update a specific setting."""
    db = get_settings_db()
    tracker = get_status_tracker()

    if request.method == "GET":
        value = db.get(key)
        return jsonify({"key": key, "value": value})

    elif request.method == "POST":
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Missing 'value' in request body"}), 400
        
        _logger.info(f"🔧 [DEBUG] Setting '{key}' changed to: {data['value']}")
        db.set(key, data["value"])
        _logger.info(f"🔧 [DEBUG] Setting '{key}' saved to DB successfully")
        
        # Update countdown/repeat mode after EVERY setting save (FIX v2.5.3, DEBUG v2.5.4, FIX v2.5.6)
        # This ensures countdown is always in sync with DB, regardless of race conditions
        try:
            _logger.info(f"🔧 [DEBUG] Reading settings from DB...")
            # CRITICAL FIX v2.5.6: Use get_all() to get correct DEFAULT_SETTINGS
            db_settings = db.get_all()
            repeat_forever = db_settings.get("repeat_forever")
            repeat_after_minutes = db_settings.get("repeat_after_minutes")
            
            _logger.info(f"🔧 [DEBUG] DB values: repeat_forever={repeat_forever}, repeat_after_minutes={repeat_after_minutes}")
            
            # Update tracker with current DB state
            _logger.info(f"🔧 [DEBUG] Calling tracker.set_repeat_mode({repeat_forever}, interval={repeat_after_minutes})...")
            tracker.set_repeat_mode(bool(repeat_forever), interval_minutes=int(repeat_after_minutes))
            
            # FIX v2.5.13: Always update next_run if repeat_forever is enabled and interval > 0
            # This ensures the progressbar uses the correct interval
            if repeat_forever and repeat_after_minutes > 0:
                _logger.info(f"🔧 [DEBUG] Calling tracker.set_next_run({repeat_after_minutes})...")
                tracker.set_next_run(int(repeat_after_minutes))
                _logger.info(f"🔧 [DEBUG] ✓ tracker.set_next_run() completed successfully!")
            else:
                _logger.info(f"🔧 [DEBUG] Clearing next_run (repeat_forever={repeat_forever}, minutes={repeat_after_minutes})")
                tracker.clear_next_run()
                
        except Exception as e:
            # Don't break on tracker update errors
            _logger.error(f"🔧 [DEBUG] ❌ EXCEPTION in tracker update: {e}", exc_info=True)
        
        tracker.add_notification("success", "Setting Updated", f"'{key}' has been updated")
        return jsonify({"status": "saved", "key": key, "value": data["value"]})

    return jsonify({"error": "Method not allowed"}), 405

@settings_bp.route("/performance", methods=["GET", "POST"])
def performance():
    """Get or update performance settings."""
    db = get_settings_db()
    tracker = get_status_tracker()

    if request.method == "GET":
        return jsonify({
            "parallel_extractions": db.get("parallel_extractions", 1),
            "cpu_cores_per_extraction": db.get("cpu_cores_per_extraction", 2),
            "auto_detect_hardware": db.get("auto_detect_hardware", True),
            "max_ram_usage_percent": db.get("max_ram_usage_percent", 75),
            "min_free_ram_gb": db.get("min_free_ram_gb", 4.0),
            "ssd_only_parallel": db.get("ssd_only_parallel", True),
        })

    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update performance settings
        for key in [
            "parallel_extractions",
            "cpu_cores_per_extraction",
            "auto_detect_hardware",
            "max_ram_usage_percent",
            "min_free_ram_gb",
            "ssd_only_parallel",
        ]:
            if key in data:
                db.set(key, data[key])

        tracker.add_notification("success", "Performance Settings Updated", "Settings will apply on next run")
        return jsonify({"status": "saved"})

    return jsonify({"error": "Method not allowed"}), 405

