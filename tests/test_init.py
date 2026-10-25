from __future__ import annotations

from pathlib import Path

import pytest
from keyring.errors import KeyringError
from typer.testing import CliRunner

from gehrman.cli import app
from gehrman.config import load_config
from gehrman.constants import KEYRING_ANTHROPIC_USERNAME, KEYRING_SERVICE, ExperienceLevel, Skill
from gehrman.paths import config_path
from tests.conftest import MemoryKeyring

runner = CliRunner()


def _init_args(**overrides: object) -> list[str]:
    args = [
        "init",
        "--experience",
        "beginner",
        "--skill",
        "web",
        "--skill",
        "api",
        "--bounty-only",
        "--force",
    ]
    extra = overrides.get("extra")
    if isinstance(extra, list):
        args.extend(extra)
    return args


def test_init_writes_config_without_secrets(
    isolated_dirs: dict[str, Path], memory_keyring: MemoryKeyring
) -> None:
    result = runner.invoke(app, _init_args(extra=["--api-key", "sk-test-1234"]))
    assert result.exit_code == 0, result.output
    config = load_config()
    assert config.profile.experience == ExperienceLevel.BEGINNER
    assert config.profile.skills == [Skill.WEB, Skill.API]
    assert config.profile.bounty_only is True
    assert config.defenses.sanitize is True
    text = config_path().read_text(encoding="utf-8")
    assert "sk-test-1234" not in text
    assert (
        memory_keyring.get_password(KEYRING_SERVICE, KEYRING_ANTHROPIC_USERNAME) == "sk-test-1234"
    )


def test_init_without_api_key_still_writes_config(
    isolated_dirs: dict[str, Path], memory_keyring: MemoryKeyring
) -> None:
    result = runner.invoke(app, _init_args())
    assert result.exit_code == 0, result.output
    assert load_config().profile.skills == [Skill.WEB, Skill.API]
    assert memory_keyring.store == {}


def test_init_keyring_failure_does_not_write_key_to_disk(
    isolated_dirs: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise KeyringError("no backend")

    monkeypatch.setattr("gehrman.secrets.keyring.set_password", boom)
    result = runner.invoke(app, _init_args(extra=["--api-key", "sk-should-not-be-on-disk"]))
    assert result.exit_code == 0, result.output
    text = config_path().read_text(encoding="utf-8")
    assert "sk-should-not-be-on-disk" not in text
    assert "ANTHROPIC_API_KEY" in result.output


def test_init_rejects_unknown_skill(isolated_dirs: dict[str, Path]) -> None:
    result = runner.invoke(
        app,
        ["init", "--experience", "beginner", "--skill", "firmware", "--force"],
    )
    assert result.exit_code != 0


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
