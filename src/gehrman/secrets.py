"""API key storage: OS keyring first, environment variable as fallback.

Security decisions:
- The Anthropic key is never written to config.toml or the audit log.
- keyring is preferred because it uses the platform secret store
  (Keychain / Secret Service / Windows Credential Locker).
- ANTHROPIC_API_KEY is accepted so CI and headless environments can run
  without a keyring backend. Callers must not print the value.
"""

from __future__ import annotations

import logging
import os

import keyring
from keyring.errors import KeyringError

from gehrman.constants import (
    ANTHROPIC_API_KEY_ENV,
    KEYRING_ANTHROPIC_USERNAME,
    KEYRING_SERVICE,
)

logger = logging.getLogger(__name__)


class SecretStoreError(RuntimeError):
    """Raised when the keyring backend cannot store a secret."""


def store_anthropic_key(api_key: str) -> None:
    """Persist the Anthropic API key in the OS keyring.

    Raises SecretStoreError if the backend is missing or refuses the write.
    The caller should then tell the user to set ANTHROPIC_API_KEY instead.
    """
    cleaned = api_key.strip()
    if not cleaned:
        raise ValueError("API key must not be empty")
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_ANTHROPIC_USERNAME, cleaned)
    except KeyringError as exc:
        logger.warning("keyring backend refused to store the API key")
        raise SecretStoreError("Unable to store the API key in the OS keyring") from exc


def get_anthropic_key() -> str | None:
    """Return the Anthropic API key, or None if neither source has one.

    Order: OS keyring, then ANTHROPIC_API_KEY. The value is never logged.
    """
    try:
        stored = keyring.get_password(KEYRING_SERVICE, KEYRING_ANTHROPIC_USERNAME)
    except KeyringError:
        logger.warning("keyring backend unavailable; falling back to %s", ANTHROPIC_API_KEY_ENV)
        stored = None
    if stored:
        return stored
    env_value = os.environ.get(ANTHROPIC_API_KEY_ENV, "").strip()
    return env_value or None


def delete_anthropic_key() -> None:
    """Remove the key from the keyring. Used by tests; ignore missing keys."""
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_ANTHROPIC_USERNAME)
    except KeyringError:
        return
