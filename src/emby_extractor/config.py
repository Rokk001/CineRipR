"""Configuration handling for emby_extractor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older versions
    tomllib = None  # type: ignore[assignment]


class ConfigurationError(RuntimeError):
    """Raised when configuration values are missing or invalid."""


@dataclass(frozen=True)
class Paths:
    """Container holding all directory paths used by the extractor."""

    download_root: Path
    extracted_root: Path
    finished_root: Path

    def ensure_ready(self) -> None:
        if not self.download_root.exists():
            raise FileNotFoundError(
                f"Download directory '{self.download_root}' does not exist."
            )
        if not self.download_root.is_dir():
            raise NotADirectoryError(
                f"Download path '{self.download_root}' is not a directory."
            )
        for target in (self.extracted_root, self.finished_root):
            target.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class SubfolderPolicy:
    """Controls which named subdirectories inside a release are processed."""

    include_sample: bool = False
    include_sub: bool = False
    include_other: bool = False

    @property
    def include_any(self) -> bool:
        return self.include_sample or self.include_sub or self.include_other


@dataclass(frozen=True)
class Settings:
    """High level settings controlling the extractor behavior."""

    paths: Paths
    retention_days: int = 14
    enable_delete: bool = False
    demo_mode: bool = False
    subfolders: SubfolderPolicy = SubfolderPolicy()
    seven_zip_path: Path | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any], *, base_path: Path | None = None) -> "Settings":
        base_path = base_path or Path.cwd()

        try:
            raw_paths = data["paths"]
        except KeyError as exc:  # pragma: no cover - config error path
            raise ConfigurationError("Missing 'paths' section in configuration") from exc
        if not isinstance(raw_paths, dict):
            raise ConfigurationError("'paths' section must be a mapping")

        def resolve_path(value: Any, *, field: str) -> Path:
            if not isinstance(value, (str, Path)):
                raise ConfigurationError(f"Path '{field}' must be a string-like value")
            path = Path(value)
            if not path.is_absolute():
                path = (base_path / path).resolve()
            return path

        try:
            download_root = resolve_path(raw_paths["download_root"], field="download_root")
            extracted_root = resolve_path(raw_paths["extracted_root"], field="extracted_root")
            finished_root = resolve_path(raw_paths["finished_root"], field="finished_root")
        except KeyError as exc:
            raise ConfigurationError(
                "paths section must define download_root, extracted_root and finished_root"
            ) from exc

        paths = Paths(
            download_root=download_root,
            extracted_root=extracted_root,
            finished_root=finished_root,
        )

        options = data.get("options", data)
        retention_days = _read_int(options, "finished_retention_days", default=14, minimum=0)
        enable_delete = _read_bool(options, "enable_delete", default=False)
        demo_mode = _read_bool(options, "demo_mode", default=False)

        subfolders_data = data.get("subfolders")
        if subfolders_data is None:
            subfolder_policy = SubfolderPolicy()
        else:
            if not isinstance(subfolders_data, dict):
                raise ConfigurationError("'subfolders' section must be a mapping")
            subfolder_policy = SubfolderPolicy(
                include_sample=_read_bool(subfolders_data, "include_sample", default=False),
                include_sub=_read_bool(subfolders_data, "include_sub", default=False),
                include_other=_read_bool(subfolders_data, "include_other", default=False),
            )

        seven_zip_path: Path | None = None
        tools_data = data.get("tools")
        if isinstance(tools_data, dict) and "seven_zip" in tools_data:
            raw_value = tools_data["seven_zip"]
            if isinstance(raw_value, (str, Path)):
                raw_text = str(raw_value).strip()
                if raw_text:
                    candidate = Path(raw_text)
                    if candidate.is_absolute() or any(sep in raw_text for sep in ("/", "\\", ":")):
                        if not candidate.is_absolute():
                            candidate = (base_path / candidate).resolve()
                        seven_zip_path = candidate
                    else:
                        seven_zip_path = candidate

        return cls(
            paths=paths,
            retention_days=retention_days,
            enable_delete=enable_delete,
            demo_mode=demo_mode,
            subfolders=subfolder_policy,
            seven_zip_path=seven_zip_path,
        )


def _read_int(data: dict[str, Any], key: str, *, default: int, minimum: int | None = None) -> int:
    value = data.get(key, default)
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"Configuration value '{key}' must be an integer") from exc
    if minimum is not None and number < minimum:
        raise ConfigurationError(f"Configuration value '{key}' must be >= {minimum}")
    return number


def _read_bool(data: dict[str, Any], key: str, *, default: bool = False) -> bool:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    raise ConfigurationError(f"Cannot interpret value '{value!r}' for '{key}' as boolean")


def load_settings(config_file: Path | None) -> Settings:
    """Load configuration from a TOML file."""

    if config_file is None:
        raise ConfigurationError("No configuration file supplied")

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file '{config_file}' does not exist")

    if tomllib is None:
        raise ConfigurationError("tomllib is not available on this Python version")

    with config_file.open("rb") as fh:
        data = tomllib.load(fh)

    if not isinstance(data, dict):  # pragma: no cover - defensive
        raise ConfigurationError("Configuration file must define a mapping at top level")

    return Settings.from_mapping(data, base_path=config_file.parent)


__all__ = [
    "ConfigurationError",
    "Paths",
    "SubfolderPolicy",
    "Settings",
    "load_settings",
]
