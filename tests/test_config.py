from __future__ import annotations

from pathlib import Path

import pytest

from cineripr.config import ConfigurationError, Settings, load_settings


def write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "config.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def test_load_settings(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
[paths]
download_root = "./downloads"
extracted_root = "./extracted"
finished_root = "./finished"

[options]
finished_retention_days = 7
enable_delete = true
demo_mode = true

[subfolders]
include_sample = true
include_sub = false
include_other = true

[tools]
seven_zip = "tools/7z.exe"
"""
    )

    settings = load_settings(config_path)
    assert isinstance(settings, Settings)
    assert settings.retention_days == 7
    assert settings.enable_delete is True
    assert settings.demo_mode is True
    assert settings.paths.download_root == (config_path.parent / "downloads").resolve()
    assert settings.subfolders.include_sample is True
    assert settings.subfolders.include_sub is False
    assert settings.subfolders.include_other is True
    assert settings.seven_zip_path == (config_path.parent / "tools" / "7z.exe").resolve()


def test_invalid_config_raises(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
[paths]
extracted_root = "./extracted"
finished_root = "./finished"
"""
    )

    with pytest.raises(ConfigurationError):
        load_settings(config_path)