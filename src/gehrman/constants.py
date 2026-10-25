"""Fixed enumerations and defaults used across Gehrman.

Keeping the skill list and experience levels here (not in free-form config)
so later tool arguments can reuse the same closed set. Categorical values
must stay enumerable: open strings are harder to validate and easier to
abuse as an injection surface.
"""

from __future__ import annotations

from enum import StrEnum

# OS keyring identifiers. The API key is never written to config.toml.
KEYRING_SERVICE = "gehrman"
KEYRING_ANTHROPIC_USERNAME = "anthropic_api_key"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

CONFIG_DIR_ENV = "GEHRMAN_CONFIG_DIR"
DATA_DIR_ENV = "GEHRMAN_DATA_DIR"

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_MAX_TOOL_STEPS = 6
DEFAULT_MAX_TOKENS_PER_MESSAGE = 8000
DEFAULT_TEXT_TRUNCATE = 1000
DEFAULT_TIME_UNIT = "hours"
DEFAULT_WEIGHTS_VERSION = "1"


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Skill(StrEnum):
    WEB = "web"
    API = "api"
    MOBILE = "mobile"
    CLOUD = "cloud"
    IOT = "iot"
    SOURCE_CODE = "source_code"
    AI = "ai"


class Provider(StrEnum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


SKILL_VALUES = tuple(skill.value for skill in Skill)
EXPERIENCE_VALUES = tuple(level.value for level in ExperienceLevel)
