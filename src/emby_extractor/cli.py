"""Command line interface for the emby extractor."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .archives import ProcessResult, process_downloads, resolve_seven_zip_command
from .cleanup import cleanup_finished
from .config import ConfigurationError, Paths, Settings, SubfolderPolicy, load_settings

DEFAULT_CONFIG = Path("emby_extractor.toml")
_LOGGER = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract archives and clean finished directory")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument("--download-root", type=Path, help="Override download directory root")
    parser.add_argument("--extracted-root", type=Path, help="Override extracted directory root")
    parser.add_argument("--finished-root", type=Path, help="Override finished directory root")
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
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
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
        paths = Paths(
            download_root=args.download_root.resolve(),
            extracted_root=paths.extracted_root,
            finished_root=paths.finished_root,
        )
    if args.extracted_root is not None:
        paths = Paths(
            download_root=paths.download_root,
            extracted_root=args.extracted_root.resolve(),
            finished_root=paths.finished_root,
        )
    if args.finished_root is not None:
        paths = Paths(
            download_root=paths.download_root,
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

    return Settings(
        paths=paths,
        retention_days=retention_days,
        enable_delete=enable_delete,
        demo_mode=demo_mode,
        subfolders=subfolders,
        seven_zip_path=seven_zip_path,
    )


def _log_path_summary(log_fn, label: str, paths: Sequence[Path], *, limit: int = 5) -> None:
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
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    try:
        settings = load_and_merge_settings(args)
    except (ConfigurationError, FileNotFoundError) as exc:
        _LOGGER.error("Configuration error: %s", exc)
        return 1

    if resolve_seven_zip_command(settings.seven_zip_path) is None:
        _LOGGER.error("7-Zip executable not found. Configure [tools].seven_zip or install 7-Zip.")
        return 1

    try:
        settings.paths.ensure_ready()
    except Exception as exc:
        _LOGGER.error("Path validation failed: %s", exc)
        return 1

    if settings.demo_mode:
        _LOGGER.warning("Demo mode enabled: no files will be extracted, moved, or deleted.")
    elif not settings.enable_delete:
        _LOGGER.info("Delete switch disabled: finished cleanup will not remove files.")

    try:
        result: ProcessResult = process_downloads(
            settings.paths,
            demo_mode=settings.demo_mode,
            seven_zip_path=settings.seven_zip_path,
            subfolders=settings.subfolders,
        )
    except Exception as exc:
        _LOGGER.error("Processing error: %s", exc)
        return 1

    deleted, cleanup_failed, skipped_cleanup = cleanup_finished(
        settings.paths.finished_root,
        settings.retention_days,
        enable_delete=settings.enable_delete,
        demo_mode=settings.demo_mode,
    )

    _LOGGER.info("Processed archives: %s", result.processed)
    if settings.demo_mode:
        _LOGGER.info("Demo mode: all actions were simulated only.")

    _log_path_summary(_LOGGER.error, "Failed archives", result.failed)
    _log_path_summary(_LOGGER.warning, "Unsupported files", result.unsupported)
    _log_path_summary(_LOGGER.info, "Deleted finished files", deleted)
    _log_path_summary(_LOGGER.info, "Skipped finished files", skipped_cleanup)
    _log_path_summary(_LOGGER.error, "Failed to clean finished directory", cleanup_failed)

    if result.failed or cleanup_failed:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
