"""Shared fixtures. Tests never touch the real home directory or keyring."""

from __future__ import annotations

from pathlib import Path

import pytest

from gehrman.constants import CONFIG_DIR_ENV, DATA_DIR_ENV


@pytest.fixture
def isolated_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Point config and data paths at a temporary tree."""
    config = tmp_path / "config"
    data = tmp_path / "data"
    monkeypatch.setenv(CONFIG_DIR_ENV, str(config))
    monkeypatch.setenv(DATA_DIR_ENV, str(data))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    return {"config": config, "data": data}


class MemoryKeyring:
    """In-process keyring substitute so tests do not use the OS store."""

    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        self.store.pop((service, username), None)


@pytest.fixture
def memory_keyring(monkeypatch: pytest.MonkeyPatch) -> MemoryKeyring:
    backend = MemoryKeyring()
    monkeypatch.setattr("gehrman.secrets.keyring.set_password", backend.set_password)
    monkeypatch.setattr("gehrman.secrets.keyring.get_password", backend.get_password)
    monkeypatch.setattr("gehrman.secrets.keyring.delete_password", backend.delete_password)
    return backend
