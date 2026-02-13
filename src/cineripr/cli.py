from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
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
        "--movie-root", type=Path, help="Override movie directory root"
    )
    parser.add_argument(
        "--tvshow-root", type=Path, help="Override TV show directory root"
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

    # Get optional movie_root and tvshow_root from CLI args or settings
    if args.movie_root is None:
        movie_root = settings.paths.movie_root if settings else None
    else:
        movie_root = args.movie_root.resolve()

    if args.tvshow_root is None:
        tvshow_root = settings.paths.tvshow_root if settings else None
    else:
        tvshow_root = args.tvshow_root.resolve()

    paths = Paths(
        download_roots=download_roots,
        extracted_root=extracted_root,
        finished_root=finished_root,
        movie_root=movie_root,
        tvshow_root=tvshow_root,
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
    # These override TOML/CLI settings (HIGHEST PRIORITY)
    try:
        from .web.settings_db import get_settings_db, DEFAULT_SETTINGS

        db = get_settings_db()

        # Load all settings with defaults applied automatically
        # This ensures DEFAULT_SETTINGS are used if DB values don't exist
        db_settings = db.get_all()

        # Override with WebGUI settings (with defaults already applied)
        repeat_forever = bool(db_settings.get("repeat_forever", repeat_forever))
        repeat_after_minutes = int(db_settings.get("repeat_after_minutes", 30))

        # Ensure minimum delay of 1 minute to prevent infinite loops
        # CRITICAL: If DB has 0 (from old version), use default 30
        if repeat_after_minutes < 1:
            _LOGGER.warning(
                "repeat_after_minutes was %d, setting to 30 (default)",
                repeat_after_minutes,
            )
            repeat_after_minutes = 30

        retention_days = int(db_settings.get("finished_retention_days", retention_days))
        enable_delete = bool(db_settings.get("enable_delete", enable_delete))
        demo_mode = bool(db_settings.get("demo_mode", demo_mode))

        # Subfolders
        include_sample = bool(
            db_settings.get("include_sample", subfolders.include_sample)
        )
        include_sub = bool(db_settings.get("include_sub", subfolders.include_sub))
        include_other = bool(db_settings.get("include_other", subfolders.include_other))
        subfolders = SubfolderPolicy(
            include_sample=include_sample,
            include_sub=include_sub,
            include_other=include_other,
        )
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

    seven_zip_cmd = resolve_seven_zip_command(settings.seven_zip_path)
    if seven_zip_cmd is None:
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
            _LOGGER.error(
                "WebGUI thread died unexpectedly. Check logs above for errors."
            )

    tracker = get_status_tracker()

    # Set repeat mode and countdown in tracker (NEW in v2.1.0, FIXED in v2.4.1, v2.5.1, v2.5.5)
    # Always set these, even if repeat_forever is False initially
    # WebGUI settings might override this later
    tracker.set_repeat_mode(
        settings.repeat_forever, interval_minutes=settings.repeat_after_minutes
    )

    tracker.configure_system_health_sources(
        downloads_path=(
            settings.paths.download_roots[0] if settings.paths.download_roots else None
        ),
        extracted_path=settings.paths.extracted_root,
        finished_path=settings.paths.finished_root,
        seven_zip_cmd=seven_zip_cmd,
    )

    # Set initial next run time so countdown is visible from start
    # This ensures countdown is visible even after container restarts
    _LOGGER.info(
        "DEBUG: repeat_forever=%s, repeat_after_minutes=%s",
        settings.repeat_forever,
        settings.repeat_after_minutes,
    )

    if settings.repeat_forever and settings.repeat_after_minutes > 0:
        tracker.set_next_run(settings.repeat_after_minutes)
        _LOGGER.info(
            "✓ Next run scheduled in %d minute(s)", settings.repeat_after_minutes
        )
    elif settings.repeat_forever and settings.repeat_after_minutes <= 0:
        # FALLBACK: If repeat_forever is true but repeat_after_minutes is invalid, use default
        _LOGGER.warning(
            "repeat_after_minutes is %d but repeat_forever is True, using default 30",
            settings.repeat_after_minutes,
        )
        tracker.set_next_run(30)
        _LOGGER.info("✓ Next run scheduled in 30 minute(s) (default)")
    else:
        _LOGGER.info("Manual mode: repeat_forever is disabled")

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

    def run_once() -> tuple[int, ProcessResult | None]:
        # Display tool name and version at the start of each loop
        _LOGGER.info("CineRipR %s", __version__)
        tracker.start_processing()

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

            # Get parallel extraction settings from WebGUI DB if available
            parallel_extractions = 1
            if args.webgui:
                try:
                    from .web.settings_db import get_settings_db

                    db = get_settings_db()
                    parallel_extractions = db.get("parallel_extractions", 1)
                except Exception:
                    pass

            result: ProcessResult = process_downloads(
                settings.paths,
                demo_mode=settings.demo_mode,
                seven_zip_path=settings.seven_zip_path,
                subfolders=settings.subfolders,
                debug=args.debug,
                status_callback=status_callback if args.webgui else None,
                parallel_extractions=parallel_extractions,
                tmdb_api_token=settings.tmdb_api_token,
            )
            tracker.update_counts(
                processed=result.processed,
                failed=len(result.failed),
                unsupported=len(result.unsupported),
            )

            # Add to history if WebGUI is enabled
            # Clear current release when done
            if args.webgui:
                with tracker._lock:
                    tracker._status.current_release = None

            tracker.stop_processing()

            # Set next run time after processing completes (if repeat mode is enabled)
            if (
                args.webgui
                and settings.repeat_forever
                and settings.repeat_after_minutes > 0
            ):
                tracker.set_next_run(settings.repeat_after_minutes)

            # Send completion notification
            if args.webgui and result.processed > 0:
                tracker.add_notification(
                    "success",
                    "Processing Complete",
                    f"Successfully processed {result.processed} archive(s)",
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

                tracker.update_counts(
                    deleted=len(deleted), cleanup_failed=len(cleanup_failed)
                )
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
            tracker.add_log("ERROR", f"Unexpected error: {exc}")
            # CRITICAL FIX v2.5.14: Ensure processing is stopped after error
            # This prevents "Processing" status from staying active and high CPU usage
            tracker.stop_processing()

        # Check repeat_forever from DB if WebGUI is enabled (FIX v2.5.5)
        repeat_forever_check = settings.repeat_forever
        if args.webgui:
            try:
                from .web.settings_db import get_settings_db

                db = get_settings_db()
                repeat_forever_check = bool(
                    db.get("repeat_forever", settings.repeat_forever)
                )
            except Exception:
                pass

        if not repeat_forever_check:
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
        # CRITICAL FIX v2.5.5: Always read from DB, not from settings object!
        # This ensures WebGUI changes are immediately reflected
        delay = max(1, int(settings.repeat_after_minutes))  # Minimum 1 minute
        if args.webgui:
            try:
                from .web.settings_db import get_settings_db

                db = get_settings_db()
                # Read fresh from DB
                db_repeat_forever = db.get("repeat_forever", settings.repeat_forever)
                db_repeat_after_minutes = db.get(
                    "repeat_after_minutes", settings.repeat_after_minutes
                )

                # Update settings object for this iteration
                settings.repeat_forever = bool(db_repeat_forever)
                settings.repeat_after_minutes = int(db_repeat_after_minutes)

                # Use DB value for delay
                delay = max(1, int(db_repeat_after_minutes))

                # Update tracker with DB values
                tracker.set_repeat_mode(settings.repeat_forever, interval_minutes=delay)
            except Exception as e:
                _LOGGER.debug(f"Failed to read settings from DB in loop: {e}")

        if delay < 1:
            _LOGGER.warning("Delay must be >= 1 minute, using 1 minute")
            delay = 1
        try:
            import time

            # Set next run time in tracker (NEW in v2.1.0, FIXED in v2.5.5)
            tracker.set_next_run(delay)

            _LOGGER.info("💤 Next run scheduled in %s minute(s)...", delay)
            tracker.add_log("INFO", f"Next run in {delay} minute(s)")

            # Check for manual trigger BEFORE sleep (FIX v2.5.8)
            if tracker.should_trigger_now():
                _LOGGER.info("⚡ Manual trigger received - starting run now!")
                tracker.add_log("INFO", "Manual trigger - starting immediately")
            else:
                # Sleep with live countdown updates
                end_time = time.time() + (delay * 60)
                last_settings_check = 0
                last_minute_logged = -1

                while time.time() < end_time:
                    # Check for manual trigger (NEW in v2.1.0)
                    if tracker.should_trigger_now():
                        _LOGGER.info("⚡ Manual trigger received - starting run now!")
                        tracker.add_log("INFO", "Manual trigger - starting immediately")
                        break

                    # Check if settings changed during sleep (FIX v2.5.5)
                    # OPTIMIZATION v2.5.17: Only check every 30 seconds instead of 5 to reduce CPU usage
                    # This reduces DB queries from ~12/min to ~2/min, significantly lowering idle CPU
                    if args.webgui and time.time() - last_settings_check >= 30:
                        try:
                            from .web.settings_db import get_settings_db

                            db = get_settings_db()
                            db_repeat_forever = db.get(
                                "repeat_forever", settings.repeat_forever
                            )
                            db_repeat_after_minutes = db.get(
                                "repeat_after_minutes", settings.repeat_after_minutes
                            )

                            # If settings changed, update tracker and recalculate end_time
                            if db_repeat_after_minutes != delay:
                                _LOGGER.info(
                                    f"⚙️ Settings changed during sleep: {delay} → {db_repeat_after_minutes} minutes"
                                )
                                settings.repeat_after_minutes = int(
                                    db_repeat_after_minutes
                                )
                                delay = max(1, int(db_repeat_after_minutes))
                                tracker.set_repeat_mode(
                                    bool(db_repeat_forever), interval_minutes=delay
                                )
                                tracker.set_next_run(delay)
                                # Recalculate end_time with new delay
                                end_time = time.time() + (delay * 60)
                                _LOGGER.info(
                                    f"💤 Next run rescheduled in %s minute(s)...", delay
                                )
                        except Exception as e:
                            _LOGGER.debug(f"Failed to check settings during sleep: {e}")
                        last_settings_check = time.time()

                    remaining = end_time - time.time()

                    # Log every minute (OPTIMIZATION v2.5.17: Only log once per minute, not every second)
                    current_minute = int(remaining / 60)
                    if current_minute != last_minute_logged and remaining > 0:
                        mins_left = int(remaining / 60)
                        if mins_left > 0:
                            _LOGGER.info(f"⏳ {mins_left} minute(s) until next run...")
                        last_minute_logged = current_minute

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
