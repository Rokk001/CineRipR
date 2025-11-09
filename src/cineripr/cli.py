from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .config import ConfigurationError, Paths, Settings, SubfolderPolicy, load_settings
from .core import ProcessResult, cleanup_finished, process_downloads
from .extraction import resolve_seven_zip_command
from .web import get_status_tracker, run_webgui

DEFAULT_CONFIG = Path("cineripr.toml")
_LOGGER = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract archives and clean finished directory"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file (optional - if not provided, use CLI args only)",
    )
    parser.add_argument(
        "--download-root",
        type=Path,
        action="append",
        help="Override download directory root (repeatable)",
    )
    parser.add_argument(
        "--extracted-root", type=Path, help="Override extracted directory root"
    )
    parser.add_argument(
        "--finished-root", type=Path, help="Override finished directory root"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        help="Override number of days after which finished files are deleted",
    )
    parser.add_argument(
        "--enable-delete",
        action=argparse.BooleanOptionalAction,
        help="Enable deletion of old files in the finished directory",
    )
    parser.add_argument(
        "--demo",
        dest="demo_mode",
        action=argparse.BooleanOptionalAction,
        help="Enable demo mode (only log actions without modifying files)",
    )
    parser.add_argument(
        "--include-sample",
        dest="include_sample",
        action=argparse.BooleanOptionalAction,
        help="Process subfolder named 'Sample' when present",
    )
    parser.add_argument(
        "--include-sub",
        dest="include_sub",
        action=argparse.BooleanOptionalAction,
        help="Process subfolder named 'Sub' when present",
    )
    parser.add_argument(
        "--include-other",
        dest="include_other",
        action=argparse.BooleanOptionalAction,
        help="Process any other subdirectories inside a release folder",
    )
    parser.add_argument(
        "--seven-zip",
        type=Path,
        help="Path or executable name for 7-Zip used to extract RAR archives",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the root log level",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug output for directory processing",
    )
    # Overrides for repeat mode
    parser.add_argument(
        "--repeat-forever",
        dest="repeat_forever",
        action=argparse.BooleanOptionalAction,
        help="Repeat the whole scan/extract loop indefinitely",
    )
    parser.add_argument(
        "--repeat-after-minutes",
        dest="repeat_after_minutes",
        type=int,
        help="Sleep minutes before repeating when repeat-forever is enabled",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--webgui",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Start WebGUI server on port 8080 (default: enabled, use --no-webgui to disable)",
    )
    parser.add_argument(
        "--webgui-port",
        type=int,
        default=8080,
        help="Port for WebGUI server (default: 8080)",
    )
    parser.add_argument(
        "--webgui-host",
        type=str,
        default="0.0.0.0",
        help="Host for WebGUI server (default: 0.0.0.0)",
    )
    return parser.parse_args(argv)


def load_and_merge_settings(args: argparse.Namespace) -> Settings:
    """Load settings from TOML (if provided), CLI args, and WebGUI database.
    
    Priority order:
    1. WebGUI settings (SQLite) - highest priority
    2. CLI args
    3. TOML file (if provided)
    4. Defaults
    """
    # Step 1: Load from TOML if provided, otherwise use defaults
    settings = None
    if args.config is not None and args.config.exists():
        try:
            settings = load_settings(args.config)
        except (FileNotFoundError, ConfigurationError) as exc:
            _LOGGER.warning(f"Could not load config file {args.config}: {exc}")
            settings = None

    # Step 2: Build paths from CLI args (required if no TOML)
    if args.download_root is None or len(args.download_root) == 0:
        if settings is None:
            raise ConfigurationError(
                "Either --config file or --download-root must be provided"
            )
        download_roots = settings.paths.download_roots
    else:
        download_roots = tuple(Path(p).resolve() for p in args.download_root)

    if args.extracted_root is None:
        if settings is None:
            raise ConfigurationError(
                "Either --config file or --extracted-root must be provided"
            )
        extracted_root = settings.paths.extracted_root
    else:
        extracted_root = args.extracted_root.resolve()

    if args.finished_root is None:
        if settings is None:
            raise ConfigurationError(
                "Either --config file or --finished-root must be provided"
            )
        finished_root = settings.paths.finished_root
    else:
        finished_root = args.finished_root.resolve()

    paths = Paths(
        download_roots=download_roots,
        extracted_root=extracted_root,
        finished_root=finished_root,
    )

    # Step 3: Load other settings from TOML (if available) or use defaults
    retention_days = settings.retention_days if settings else 14
    enable_delete = settings.enable_delete if settings else False
    demo_mode = settings.demo_mode if settings else False
    subfolders = settings.subfolders if settings else SubfolderPolicy()
    seven_zip_path = settings.seven_zip_path if settings else None
    repeat_forever = settings.repeat_forever if settings else False
    repeat_after_minutes = settings.repeat_after_minutes if settings else 0

    # Step 4: Override with CLI args if provided
    if args.retention_days is not None:
        if args.retention_days < 0:
            raise ConfigurationError("Retention days cannot be negative")
        retention_days = args.retention_days

    if args.enable_delete is not None:
        enable_delete = args.enable_delete

    if args.demo_mode is not None:
        demo_mode = args.demo_mode

    include_sample = subfolders.include_sample
    include_sub = subfolders.include_sub
    include_other = subfolders.include_other

    if args.include_sample is not None:
        include_sample = args.include_sample
    if args.include_sub is not None:
        include_sub = args.include_sub
    if args.include_other is not None:
        include_other = args.include_other

    subfolders = SubfolderPolicy(
        include_sample=include_sample,
        include_sub=include_sub,
        include_other=include_other,
    )

    if args.seven_zip is not None:
        seven_zip_path = args.seven_zip

    if getattr(args, "repeat_forever", None) is not None:
        repeat_forever = bool(args.repeat_forever)

    if getattr(args, "repeat_after_minutes", None) is not None:
        if args.repeat_after_minutes < 0:
            raise ConfigurationError("repeat-after-minutes cannot be negative")
        repeat_after_minutes = int(args.repeat_after_minutes)

    # Step 5: Load WebGUI settings from SQLite database (NEW in v2.3.0)
    # These override TOML/CLI settings
    try:
        from .web.settings_db import get_settings_db

        db = get_settings_db()

        # Override with WebGUI settings if they exist
        repeat_forever_db = db.get("repeat_forever")
        if repeat_forever_db is not None:
            repeat_forever = bool(repeat_forever_db)

        repeat_after_minutes_db = db.get("repeat_after_minutes")
        if repeat_after_minutes_db is not None:
            repeat_after_minutes = int(repeat_after_minutes_db)

        retention_days_db = db.get("finished_retention_days")
        if retention_days_db is not None:
            retention_days = int(retention_days_db)

        enable_delete_db = db.get("enable_delete")
        if enable_delete_db is not None:
            enable_delete = bool(enable_delete_db)

        include_sample_db = db.get("include_sample")
        if include_sample_db is not None:
            subfolders = SubfolderPolicy(
                include_sample=bool(include_sample_db),
                include_sub=subfolders.include_sub,
                include_other=subfolders.include_other,
            )

        include_sub_db = db.get("include_sub")
        if include_sub_db is not None:
            subfolders = SubfolderPolicy(
                include_sample=subfolders.include_sample,
                include_sub=bool(include_sub_db),
                include_other=subfolders.include_other,
            )

        include_other_db = db.get("include_other")
        if include_other_db is not None:
            subfolders = SubfolderPolicy(
                include_sample=subfolders.include_sample,
                include_sub=subfolders.include_sub,
                include_other=bool(include_other_db),
            )

        demo_mode_db = db.get("demo_mode")
        if demo_mode_db is not None:
            demo_mode = bool(demo_mode_db)
    except Exception as e:
        # If database is not available, fall back to TOML/CLI settings
        _LOGGER.debug(f"Could not load WebGUI settings: {e}")

    return Settings(
        paths=paths,
        retention_days=retention_days,
        enable_delete=enable_delete,
        demo_mode=demo_mode,
        subfolders=subfolders,
        seven_zip_path=seven_zip_path,
        repeat_forever=repeat_forever,
        repeat_after_minutes=repeat_after_minutes,
    )


def _log_path_summary(
    log_fn, label: str, paths: Sequence[Path], *, limit: int = 5
) -> None:
    if not paths:
        return
    sorted_paths = sorted(paths, key=lambda path: str(path).lower())
    log_fn("%s (%s)", label, len(sorted_paths))
    for path in sorted_paths[:limit]:
        log_fn("  %s", path)
    remaining = len(sorted_paths) - limit
    if remaining > 0:
        log_fn("  ... %s more", remaining)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(message)s")

    try:
        settings = load_and_merge_settings(args)
    except (ConfigurationError, FileNotFoundError) as exc:
        _LOGGER.error("Configuration error: %s", exc)
        return 1

    # Helpful startup log to verify which config was loaded and key options
    if args.config is not None and args.config.exists():
        _LOGGER.info(
            "Using config: %s | repeat_forever=%s, repeat_after_minutes=%s, demo=%s, delete=%s",
            args.config,
            settings.repeat_forever,
            settings.repeat_after_minutes,
            settings.demo_mode,
            settings.enable_delete,
        )
    else:
        _LOGGER.info(
            "Using CLI args only | repeat_forever=%s, repeat_after_minutes=%s, demo=%s, delete=%s",
            settings.repeat_forever,
            settings.repeat_after_minutes,
            settings.demo_mode,
            settings.enable_delete,
        )

    if resolve_seven_zip_command(settings.seven_zip_path) is None:
        _LOGGER.error(
            "7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip."
        )
        return 1

    try:
        settings.paths.ensure_ready()
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        _LOGGER.error("Path validation failed: %s", exc)
        return 1

    if settings.demo_mode:
        _LOGGER.warning(
            "Demo mode enabled: no files will be extracted, moved, or deleted."
        )
    elif not settings.enable_delete:
        _LOGGER.info("Delete switch disabled: finished cleanup will not remove files.")

    # Start WebGUI (enabled by default, can be disabled with --no-webgui)
    webgui_thread = None
    if args.webgui:
        import threading
        import time

        # Check if Flask is available
        try:
            from flask import Flask
            _LOGGER.info("Flask is available, starting WebGUI...")
        except ImportError as exc:
            _LOGGER.error(
                "Flask is not installed. Install it with: pip install flask>=3.0.0"
            )
            _LOGGER.error("WebGUI cannot start: %s", exc)
            return 1

        def start_webgui() -> None:
            try:
                _LOGGER.info("WebGUI thread starting...")
                run_webgui(host=args.webgui_host, port=args.webgui_port, debug=False)
            except Exception as exc:
                _LOGGER.error("WebGUI error: %s", exc, exc_info=True)

        webgui_thread = threading.Thread(target=start_webgui, daemon=False)
        webgui_thread.start()
        # Give WebGUI time to start
        time.sleep(2)
        if webgui_thread.is_alive():
            _LOGGER.info(
                "WebGUI started on http://%s:%d", args.webgui_host, args.webgui_port
            )
        else:
            _LOGGER.error("WebGUI thread died unexpectedly. Check logs above for errors.")

    tracker = get_status_tracker()

    # Set repeat mode in tracker (NEW in v2.1.0)
    tracker.set_repeat_mode(settings.repeat_forever)
    
    # Set initial next run time so countdown is visible from start
    if settings.repeat_forever and settings.repeat_after_minutes > 0:
        tracker.set_next_run(settings.repeat_after_minutes)

    # Set up logging handler to forward logs to status tracker
    class StatusLogHandler(logging.Handler):
        """Logging handler that forwards logs to the status tracker."""

        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = record.levelname
                message = self.format(record)
                tracker.add_log(level, message)
            except Exception:
                pass  # Ignore errors in logging handler

    if args.webgui:
        status_handler = StatusLogHandler()
        status_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(status_handler)
        
        # Initialize system health immediately after WebGUI starts
        seven_zip_cmd = resolve_seven_zip_command(settings.seven_zip_path)
        seven_zip_version = "Unknown"
        if seven_zip_cmd:
            try:
                import subprocess
                import re
                # Try multiple methods to get version
                methods = [
                    # Method 1: Run without args (7zz outputs version info)
                    lambda: subprocess.run([seven_zip_cmd], capture_output=True, text=True, timeout=5),
                    # Method 2: Run with --version flag
                    lambda: subprocess.run([seven_zip_cmd, "--version"], capture_output=True, text=True, timeout=5),
                    # Method 3: Run with -v flag
                    lambda: subprocess.run([seven_zip_cmd, "-v"], capture_output=True, text=True, timeout=5),
                ]
                
                # Try multiple regex patterns for different 7-Zip output formats
                patterns = [
                    r'7-Zip\s+([\d.]+)',           # "7-Zip 24.09"
                    r'7z\s+([\d.]+)',             # "7z 24.09"
                    r'p7zip\s+([\d.]+)',          # "p7zip 16.02"
                    r'Version\s+([\d.]+)',       # "Version 24.09"
                    r'([\d]+\.[\d]+)',            # Just version number "24.09"
                ]
                
                for method in methods:
                    try:
                        result = method()
                        output = (result.stdout or "") + (result.stderr or "")
                        
                        for pattern in patterns:
                            match = re.search(pattern, output, re.IGNORECASE)
                            if match:
                                seven_zip_version = f"7-Zip {match.group(1)}"
                                break
                        
                        if seven_zip_version != "Unknown":
                            break
                    except Exception:
                        continue
            except Exception as e:
                _LOGGER.debug(f"Failed to get 7-Zip version: {e}")
                pass
        
        tracker.update_system_health(
            downloads_path=settings.paths.download_roots[0] if settings.paths.download_roots else None,
            extracted_path=settings.paths.extracted_root,
            finished_path=settings.paths.finished_root,
            seven_zip_version=seven_zip_version
        )

    def run_once() -> tuple[int, ProcessResult | None]:
        # Display tool name and version at the start of each loop
        _LOGGER.info("CineRipR %s", __version__)
        tracker.start_processing()
        
        # Update system health at start of each run (if WebGUI is enabled)
        if args.webgui:
            try:
                seven_zip_cmd = resolve_seven_zip_command(settings.seven_zip_path)
                seven_zip_version = "Unknown"
                if seven_zip_cmd:
                    try:
                        import subprocess
                        import re
                        # Try multiple methods to get version
                        methods = [
                            lambda: subprocess.run([seven_zip_cmd], capture_output=True, text=True, timeout=5),
                            lambda: subprocess.run([seven_zip_cmd, "--version"], capture_output=True, text=True, timeout=5),
                            lambda: subprocess.run([seven_zip_cmd, "-v"], capture_output=True, text=True, timeout=5),
                        ]
                        
                        patterns = [
                            r'7-Zip\s+([\d.]+)',
                            r'7z\s+([\d.]+)',
                            r'p7zip\s+([\d.]+)',
                            r'Version\s+([\d.]+)',
                            r'([\d]+\.[\d]+)',
                        ]
                        
                        for method in methods:
                            try:
                                result = method()
                                output = (result.stdout or "") + (result.stderr or "")
                                
                                for pattern in patterns:
                                    match = re.search(pattern, output, re.IGNORECASE)
                                    if match:
                                        seven_zip_version = f"7-Zip {match.group(1)}"
                                        break
                                
                                if seven_zip_version != "Unknown":
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass
                
                tracker.update_system_health(
                    downloads_path=settings.paths.download_roots[0] if settings.paths.download_roots else None,
                    extracted_path=settings.paths.extracted_root,
                    finished_path=settings.paths.finished_root,
                    seven_zip_version=seven_zip_version
                )
            except Exception as e:
                _LOGGER.debug(f"Failed to update system health at start: {e}")
        
        try:
            # Define status callback for process_downloads
            current_release_name: str | None = None
            
            def status_callback(
                status: str,
                message: str,
                current_archive: str | None,
                archive_progress: int,
                archive_total: int,
            ) -> None:
                nonlocal current_release_name
                
                # Extract release name from message if available
                if status == "scanning" and message.startswith("Processing "):
                    current_release_name = message.replace("Processing ", "")
                    tracker.set_current_release(current_release_name)
                
                # Update release status
                if tracker.get_status().current_release:
                    tracker.update_release_status(
                        status=status,
                        message=message,
                        current_archive=current_archive,
                        archive_progress=archive_progress,
                        archive_total=archive_total,
                    )
                elif current_release_name:
                    # Use actual release name if available
                    tracker.set_current_release(current_release_name)
                    tracker.update_release_status(
                        status=status,
                        message=message,
                        current_archive=current_archive,
                        archive_progress=archive_progress,
                        archive_total=archive_total,
                    )
                else:
                    # Fallback: Create a dummy release for status updates
                    tracker.set_current_release("Processing...")
                    tracker.update_release_status(
                        status=status,
                        message=message,
                        current_archive=current_archive,
                        archive_progress=archive_progress,
                        archive_total=archive_total,
                    )

            result: ProcessResult = process_downloads(
                settings.paths,
                demo_mode=settings.demo_mode,
                seven_zip_path=settings.seven_zip_path,
                subfolders=settings.subfolders,
                debug=args.debug,
                status_callback=status_callback if args.webgui else None,
            )
            tracker.update_counts(
                processed=result.processed,
                failed=len(result.failed),
                unsupported=len(result.unsupported),
            )
            
            # Add to history if WebGUI is enabled
            if args.webgui:
                # Calculate duration
                duration = 0.0
                if tracker._status.start_time:
                    from datetime import datetime
                    duration = (datetime.now() - tracker._status.start_time).total_seconds()
                
                # Use current_release_name or a generic name
                release_name = current_release_name if current_release_name else "Processing Run"
                
                # Determine status
                status = "completed" if result.processed > 0 and len(result.failed) == 0 else "failed"
                
                # Add history entry
                tracker.add_to_history(
                    release_name=release_name,
                    status=status,
                    processed_archives=result.processed,
                    failed_archives=len(result.failed),
                    duration_seconds=duration,
                    extracted_files=[],
                    error_messages=[str(f) for f in result.failed[:10]]  # First 10 errors
                )
                
                # Clear current release when done
                with tracker._lock:
                    tracker._status.current_release = None
            
            tracker.stop_processing()
            
            # Set next run time after processing completes (if repeat mode is enabled)
            if args.webgui and settings.repeat_forever and settings.repeat_after_minutes > 0:
                tracker.set_next_run(settings.repeat_after_minutes)
            
            # Update system health after processing (if WebGUI is enabled)
            if args.webgui:
                try:
                    seven_zip_cmd = resolve_seven_zip_command(settings.seven_zip_path)
                    seven_zip_version = "Unknown"
                    if seven_zip_cmd:
                        try:
                            import subprocess
                            import re
                            methods = [
                                lambda: subprocess.run([seven_zip_cmd], capture_output=True, text=True, timeout=5),
                                lambda: subprocess.run([seven_zip_cmd, "--version"], capture_output=True, text=True, timeout=5),
                                lambda: subprocess.run([seven_zip_cmd, "-v"], capture_output=True, text=True, timeout=5),
                            ]
                            
                            patterns = [
                                r'7-Zip\s+([\d.]+)',
                                r'7z\s+([\d.]+)',
                                r'p7zip\s+([\d.]+)',
                                r'Version\s+([\d.]+)',
                                r'([\d]+\.[\d]+)',
                            ]
                            
                            for method in methods:
                                try:
                                    result = method()
                                    output = (result.stdout or "") + (result.stderr or "")
                                    
                                    for pattern in patterns:
                                        match = re.search(pattern, output, re.IGNORECASE)
                                        if match:
                                            seven_zip_version = f"7-Zip {match.group(1)}"
                                            break
                                    
                                    if seven_zip_version != "Unknown":
                                        break
                                except Exception:
                                    continue
                        except Exception:
                            pass
                    
                    tracker.update_system_health(
                        downloads_path=settings.paths.download_roots[0] if settings.paths.download_roots else None,
                        extracted_path=settings.paths.extracted_root,
                        finished_path=settings.paths.finished_root,
                        seven_zip_version=seven_zip_version
                    )
                except Exception as e:
                    _LOGGER.debug(f"Failed to update system health after processing: {e}")
            
            # Send completion notification
            if args.webgui and result.processed > 0:
                tracker.add_notification(
                    "success",
                    "Processing Complete",
                    f"Successfully processed {result.processed} archive(s)"
                )
            
            return 0, result
        except RuntimeError as exc:
            _LOGGER.error("Processing error: %s", exc)
            tracker.add_log("ERROR", f"Processing error: {exc}")
            tracker.stop_processing()
            return 1, None

    _LOGGER.info(
        "Repeat mode: %s, delay: %s minute(s)",
        settings.repeat_forever,
        settings.repeat_after_minutes,
    )

    exit_code = 0
    while True:
        try:
            code, result = run_once()
            exit_code = max(exit_code, code)

            deleted: list[Path]
            cleanup_failed: list[Path]
            skipped_cleanup: list[Path]

            if result is not None:
                if settings.enable_delete or settings.demo_mode:
                    deleted, cleanup_failed, skipped_cleanup = cleanup_finished(
                        settings.paths.finished_root,
                        settings.retention_days,
                        enable_delete=settings.enable_delete,
                        demo_mode=settings.demo_mode,
                    )
                else:
                    _LOGGER.info(
                        "Delete disabled and demo mode off: skipping finished cleanup scan."
                    )
                    deleted = []
                    cleanup_failed = []
                    skipped_cleanup = []

                tracker.update_counts(deleted=len(deleted), cleanup_failed=len(cleanup_failed))
                _LOGGER.info("Processed archives: %s", result.processed)
                if settings.demo_mode:
                    _LOGGER.info("Demo mode: all actions were simulated only.")

                _log_path_summary(_LOGGER.error, "Failed archives", result.failed)
                _log_path_summary(
                    _LOGGER.warning, "Unsupported files", result.unsupported
                )
                _log_path_summary(_LOGGER.info, "Deleted finished files", deleted)
                _log_path_summary(
                    _LOGGER.info, "Skipped finished files", skipped_cleanup
                )
                _log_path_summary(
                    _LOGGER.error, "Failed to clean finished directory", cleanup_failed
                )

                if result.failed or cleanup_failed:
                    exit_code = max(exit_code, 2)

        except Exception as exc:
            _LOGGER.error("Unexpected error in main loop: %s", exc)

        if not settings.repeat_forever:
            # If WebGUI is running, keep the main thread alive
            if args.webgui and webgui_thread and webgui_thread.is_alive():
                _LOGGER.info("WebGUI is running. Press Ctrl+C to exit.")
                try:
                    import time
                    while webgui_thread.is_alive():
                        time.sleep(1)
                except KeyboardInterrupt:
                    _LOGGER.info("Interrupted; exiting.")
            break

        # sleep before next iteration
        delay = max(0, int(settings.repeat_after_minutes))
        if delay <= 0:
            continue
        try:
            import time

            # Set next run time in tracker (NEW in v2.1.0)
            tracker.set_next_run(delay)

            _LOGGER.info("💤 Next run scheduled in %s minute(s)...", delay)
            tracker.add_log("INFO", f"Next run in {delay} minute(s)")

            # Sleep with live countdown updates
            end_time = time.time() + (delay * 60)
            last_system_health_update = 0

            while time.time() < end_time:
                # Check for manual trigger (NEW in v2.1.0)
                if tracker.should_trigger_now():
                    _LOGGER.info("⚡ Manual trigger received - starting run now!")
                    tracker.add_log("INFO", "Manual trigger - starting immediately")
                    break

                remaining = end_time - time.time()

                # Update system health every 30 seconds (for WebGUI)
                if args.webgui and time.time() - last_system_health_update >= 30:
                    try:
                        seven_zip_cmd = resolve_seven_zip_command(settings.seven_zip_path)
                        seven_zip_version = "Unknown"
                        if seven_zip_cmd:
                            try:
                                import subprocess
                                import re
                                # Try multiple methods to get version
                                methods = [
                                    lambda: subprocess.run([seven_zip_cmd], capture_output=True, text=True, timeout=5),
                                    lambda: subprocess.run([seven_zip_cmd, "--version"], capture_output=True, text=True, timeout=5),
                                    lambda: subprocess.run([seven_zip_cmd, "-v"], capture_output=True, text=True, timeout=5),
                                ]
                                
                                patterns = [
                                    r'7-Zip\s+([\d.]+)',
                                    r'7z\s+([\d.]+)',
                                    r'p7zip\s+([\d.]+)',
                                    r'Version\s+([\d.]+)',
                                    r'([\d]+\.[\d]+)',
                                ]
                                
                                for method in methods:
                                    try:
                                        result = method()
                                        output = (result.stdout or "") + (result.stderr or "")
                                        
                                        for pattern in patterns:
                                            match = re.search(pattern, output, re.IGNORECASE)
                                            if match:
                                                seven_zip_version = f"7-Zip {match.group(1)}"
                                                break
                                        
                                        if seven_zip_version != "Unknown":
                                            break
                                    except Exception:
                                        continue
                            except Exception:
                                pass
                        
                        tracker.update_system_health(
                            downloads_path=settings.paths.download_roots[0] if settings.paths.download_roots else None,
                            extracted_path=settings.paths.extracted_root,
                            finished_path=settings.paths.finished_root,
                            seven_zip_version=seven_zip_version
                        )
                        last_system_health_update = time.time()
                    except Exception as e:
                        _LOGGER.debug(f"Failed to update system health: {e}")

                # Log every minute
                if int(remaining) % 60 == 0 and remaining > 0:
                    mins_left = int(remaining / 60)
                    if mins_left > 0:
                        _LOGGER.info(f"⏳ {mins_left} minute(s) until next run...")

                # Sleep in 1-second chunks to allow interruption
                time.sleep(1)

            # Clear next run time
            tracker.clear_next_run()
            _LOGGER.info("⏰ Starting next run now!")

        except KeyboardInterrupt:
            _LOGGER.info("Interrupted during sleep; exiting.")
            tracker.clear_next_run()
            break

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

__all__ = ["main"]
