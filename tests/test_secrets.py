from __future__ import annotations

import pytest
from keyring.errors import KeyringError

from gehrman.constants import (
    ANTHROPIC_API_KEY_ENV,
    KEYRING_ANTHROPIC_USERNAME,
    KEYRING_SERVICE,
)
from gehrman.secrets import SecretStoreError, get_anthropic_key, store_anthropic_key
from tests.conftest import MemoryKeyring


def test_store_and_get_from_keyring(memory_keyring: MemoryKeyring) -> None:
    store_anthropic_key("  sk-test-key  ")
    assert memory_keyring.get_password(KEYRING_SERVICE, KEYRING_ANTHROPIC_USERNAME) == "sk-test-key"
    assert get_anthropic_key() == "sk-test-key"


def test_keyring_preferred_over_env(
    memory_keyring: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    store_anthropic_key("from-keyring")
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "from-env")
    assert get_anthropic_key() == "from-keyring"


def test_env_fallback_when_keyring_empty(
    memory_keyring: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "from-env")
    assert get_anthropic_key() == "from-env"


def test_none_when_neither_source_has_key(
    memory_keyring: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
    assert get_anthropic_key() is None


def test_empty_key_rejected(memory_keyring: MemoryKeyring) -> None:
    with pytest.raises(ValueError, match="empty"):
        store_anthropic_key("   ")


def test_keyring_failure_becomes_secret_store_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise KeyringError("no backend")

    monkeypatch.setattr("gehrman.secrets.keyring.set_password", boom)
    with pytest.raises(SecretStoreError):
        store_anthropic_key("sk-test")
