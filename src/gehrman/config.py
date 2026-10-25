"""Load and save the user configuration file.

The file at ~/.config/gehrman/config.toml holds researcher preferences and
defense switches. It must never contain secrets: API keys live in the OS
keyring or in ANTHROPIC_API_KEY (see gehrman.secrets).

Unknown keys are rejected so a typo in a defense switch cannot silently
disable a control during the experiment.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Self

import tomli_w
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gehrman.constants import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_MAX_TOKENS_PER_MESSAGE,
    DEFAULT_MAX_TOOL_STEPS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_TEXT_TRUNCATE,
    DEFAULT_TIME_UNIT,
    DEFAULT_WEIGHTS_VERSION,
    ExperienceLevel,
    Provider,
    Skill,
)
from gehrman.paths import config_path, ensure_private_dir

# Written at the top of every saved file as a reminder. tomli-w does not
# preserve comments on rewrite, so we prepend this on every save.
CONFIG_HEADER = (
    "# Gehrman configuration. Never store API keys or secrets in this file.\n"
    "# Secrets belong in the OS keyring or in ANTHROPIC_API_KEY.\n"
)

# Keys that must never appear in the serialized config. Used as a belt-and-
# suspenders check before writing and in tests.
FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "anthropic_api_key",
        "secret",
        "token",
        "password",
        "keyring",
    }
)


class ProfileConfig(BaseModel):
    """Researcher profile used later by opportunity scoring."""

    model_config = ConfigDict(extra="forbid")

    experience: ExperienceLevel
    skills: list[Skill] = Field(min_length=1)
    bounty_only: bool = False

    @field_validator("skills")
    @classmethod
    def _unique_skills(cls, value: list[Skill]) -> list[Skill]:
        # Preserve order while dropping duplicates.
        seen: set[Skill] = set()
        unique: list[Skill] = []
        for skill in value:
            if skill not in seen:
                seen.add(skill)
                unique.append(skill)
        return unique


class AgentConfig(BaseModel):
    """Model and loop limits. Temperature is fixed at 0 in the agent."""

    model_config = ConfigDict(extra="forbid")

    provider: Provider = Provider.ANTHROPIC
    model: str = DEFAULT_ANTHROPIC_MODEL
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    max_tool_steps: int = Field(default=DEFAULT_MAX_TOOL_STEPS, ge=1, le=DEFAULT_MAX_TOOL_STEPS)
    max_tokens_per_message: int = Field(default=DEFAULT_MAX_TOKENS_PER_MESSAGE, ge=256)
    text_truncate: int = Field(default=DEFAULT_TEXT_TRUNCATE, ge=1)


class ScoringConfig(BaseModel):
    """Scoring knobs.

    `time_unit` documents how we *display* HackerOne average_time_* values.
    The unit is undocumented upstream, so we store raw numbers and never
    convert them silently.
    """

    model_config = ConfigDict(extra="forbid")

    time_unit: str = DEFAULT_TIME_UNIT
    weights_version: str = DEFAULT_WEIGHTS_VERSION


class DefensesConfig(BaseModel):
    """Switchable layered defenses for the prompt-injection experiment.

    Defaults are on (secure). Each flag is independent so an ablation can
    disable one control at a time without touching the others.
    """

    model_config = ConfigDict(extra="forbid")

    sanitize: bool = True
    data_marking: bool = True
    ai_guard_input: bool = True
    ai_guard_output: bool = True
    scope_check: bool = True
    number_check: bool = True


class AiGuardConfig(BaseModel):
    """Separate classifier model used by ai_guard_input / ai_guard_output."""

    model_config = ConfigDict(extra="forbid")

    model: str = DEFAULT_ANTHROPIC_MODEL


class AppConfig(BaseModel):
    """Top-level configuration object persisted as TOML."""

    model_config = ConfigDict(extra="forbid")

    profile: ProfileConfig
    agent: AgentConfig = Field(default_factory=AgentConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    defenses: DefensesConfig = Field(default_factory=DefensesConfig)
    ai_guard: AiGuardConfig = Field(default_factory=AiGuardConfig)

    @model_validator(mode="after")
    def _no_secret_fields(self) -> Self:
        _assert_no_secret_keys(self.model_dump(mode="json"))
        return self


def _assert_no_secret_keys(payload: object, prefix: str = "") -> None:
    """Raise if a forbidden key name appears anywhere in the structure."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            path = f"{prefix}.{key}" if prefix else str(key)
            if lowered in FORBIDDEN_SECRET_KEYS:
                msg = (
                    f"Refusing to handle config key {path!r}: secrets do not belong in config.toml"
                )
                raise ValueError(msg)
            _assert_no_secret_keys(value, path)
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            _assert_no_secret_keys(item, f"{prefix}[{index}]")


def load_config(path: Path | None = None) -> AppConfig:
    """Read and validate config.toml. Missing file is a hard error."""
    target = path or config_path()
    if not target.is_file():
        msg = f"Config not found at {target}. Run `gehrman init` first."
        raise FileNotFoundError(msg)
    with target.open("rb") as handle:
        data = tomllib.load(handle)
    return AppConfig.model_validate(data)


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    """Validate, reject secret keys, and write config.toml."""
    payload = config.model_dump(mode="json")
    _assert_no_secret_keys(payload)
    target = path or config_path()
    ensure_private_dir(target.parent)
    body = tomli_w.dumps(payload)
    target.write_text(CONFIG_HEADER + body, encoding="utf-8")
    return target
