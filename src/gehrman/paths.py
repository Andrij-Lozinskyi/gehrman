"""Resolve config and data directories.

Default locations match the thesis spec (`~/.config/gehrman/config.toml`)
and XDG for data (`~/.local/share/gehrman`). Both can be overridden with
environment variables so tests never touch the developer's real home
directory.

Security: these paths are for local, single-user state only. Nothing under
them is a network-facing store.
"""

from __future__ import annotations

import os
from pathlib import Path

from gehrman.constants import CONFIG_DIR_ENV, DATA_DIR_ENV


def config_dir() -> Path:
    """Return the directory that holds `config.toml` (no secrets)."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "gehrman"
    return Path.home() / ".config" / "gehrman"


def config_path() -> Path:
    return config_dir() / "config.toml"


def data_dir() -> Path:
    """Return the directory for SQLite and raw snapshots (later milestones)."""
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg).expanduser() / "gehrman"
    return Path.home() / ".local" / "share" / "gehrman"


def ensure_private_dir(path: Path) -> Path:
    """Create `path` with mode 0700 so only the current user can read it.

    Config contains no secrets, but data later will hold program snapshots
    and the audit log. Restricting the directory is cheap defense in depth.
    """
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path
