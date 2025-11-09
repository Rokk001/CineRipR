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
        default=DEFAULT_CONFIG,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG})",
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
    try:
        settings = load_settings(args.config)
    except FileNotFoundError:
        raise
    except ConfigurationError:
        raise

    paths = settings.paths
    if args.download_root is not None:
        override_roots = tuple(Path(p).resolve() for p in args.download_root)
        paths = Paths(
            download_roots=override_roots,
            extracted_root=paths.extracted_root,
            finished_root=paths.finished_root,
        )
    if args.extracted_root is not None:
        paths = Paths(
            download_roots=paths.download_roots,
            extracted_root=args.extracted_root.resolve(),
            finished_root=paths.finished_root,
        )
    if args.finished_root is not None:
        paths = Paths(
            download_roots=paths.download_roots,
            extracted_root=paths.extracted_root,
            finished_root=args.finished_root.resolve(),
        )

    retention_days = settings.retention_days
    if args.retention_days is not None:
        if args.retention_days < 0:
            raise ConfigurationError("Retention days cannot be negative")
        retention_days = args.retention_days

    enable_delete = settings.enable_delete
    if args.enable_delete is not None:
        enable_delete = args.enable_delete

    demo_mode = settings.demo_mode
    if args.demo_mode is not None:
        demo_mode = args.demo_mode

    subfolders = settings.subfolders
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

    seven_zip_path = settings.seven_zip_path
    if args.seven_zip is not None:
        seven_zip_path = args.seven_zip

    # Repeat overrides from CLI
    repeat_forever = settings.repeat_forever
    if getattr(args, "repeat_forever", None) is not None:
        repeat_forever = bool(args.repeat_forever)

    repeat_after_minutes = settings.repeat_after_minutes
    if getattr(args, "repeat_after_minutes", None) is not None:
        if args.repeat_after_minutes < 0:
            raise ConfigurationError("repeat-after-minutes cannot be negative")
        repeat_after_minutes = int(args.repeat_after_minutes)

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
    _LOGGER.info(
        "Using config: %s | repeat_forever=%s, repeat_after_minutes=%s, demo=%s, delete=%s",
        args.config,
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
                result = subprocess.run(
                    [seven_zip_cmd], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                output = result.stdout + result.stderr
                import re
                match = re.search(r'7-Zip\s+([\d.]+)', output)
                if match:
                    seven_zip_version = f"7-Zip {match.group(1)}"
            except Exception:
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
        
        # Update system health at start of each run
        if args.webgui:
            # Get 7-Zip version
            seven_zip_cmd = resolve_seven_zip_command(settings.seven_zip_path)
            seven_zip_version = "Unknown"
            if seven_zip_cmd:
                try:
                    import subprocess
                    result = subprocess.run(
                        [seven_zip_cmd], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    output = result.stdout + result.stderr
                    # Extract version from output (e.g., "7-Zip 24.09")
                    import re
                    match = re.search(r'7-Zip\s+([\d.]+)', output)
                    if match:
                        seven_zip_version = f"7-Zip {match.group(1)}"
                except Exception:
                    pass
            
            tracker.update_system_health(
                downloads_path=settings.paths.download_roots[0] if settings.paths.download_roots else None,
                extracted_path=settings.paths.extracted_root,
                finished_path=settings.paths.finished_root,
                seven_zip_version=seven_zip_version
            )
        
        try:
            # Define status callback for process_downloads
            def status_callback(
                status: str,
                message: str,
                current_archive: str | None,
                archive_progress: int,
                archive_total: int,
            ) -> None:
                if tracker.get_status().current_release:
                    tracker.update_release_status(
                        status=status,
                        message=message,
                        current_archive=current_archive,
                        archive_progress=archive_progress,
                        archive_total=archive_total,
                    )
                else:
                    # Create a dummy release for status updates
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
            
            # Clear current release when done
            if args.webgui:
                with tracker._lock:
                    tracker._status.current_release = None
            
            tracker.stop_processing()
            
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

            _LOGGER.info("Sleeping for %s minute(s) before next run...", delay)
            time.sleep(delay * 60)
        except KeyboardInterrupt:
            _LOGGER.info("Interrupted during sleep; exiting.")
            break

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

__all__ = ["main"]
