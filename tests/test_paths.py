from __future__ import annotations

from pathlib import Path

import pytest

from gehrman.constants import CONFIG_DIR_ENV, DATA_DIR_ENV
from gehrman.paths import config_dir, config_path, data_dir, ensure_private_dir


def test_config_dir_uses_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "custom-config"))
    assert config_dir() == tmp_path / "custom-config"
    assert config_path() == tmp_path / "custom-config" / "config.toml"


def test_data_dir_uses_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "custom-data"))
    assert data_dir() == tmp_path / "custom-data"


def test_default_config_dir_is_under_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(CONFIG_DIR_ENV, raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert config_dir() == tmp_path / ".config" / "gehrman"


def test_xdg_config_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(CONFIG_DIR_ENV, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    assert config_dir() == tmp_path / "xdg-config" / "gehrman"


def test_ensure_private_dir_mode(tmp_path: Path) -> None:
    target = tmp_path / "private"
    ensure_private_dir(target)
    assert target.is_dir()
    assert (target.stat().st_mode & 0o777) == 0o700
