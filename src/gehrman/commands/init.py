"""Interactive (and scriptable) first-run setup.

Collects the researcher profile and optionally an Anthropic API key.
The profile is written to config.toml. The key is stored via keyring;
if that fails, the user is told to set ANTHROPIC_API_KEY instead.
"""

from __future__ import annotations

from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from gehrman.config import AppConfig, ProfileConfig, save_config
from gehrman.constants import EXPERIENCE_VALUES, SKILL_VALUES, ExperienceLevel, Skill
from gehrman.paths import config_path
from gehrman.secrets import SecretStoreError, store_anthropic_key

console = Console()


def _prompt_experience() -> ExperienceLevel:
    raw = typer.prompt(f"Experience level [{'/'.join(EXPERIENCE_VALUES)}]")
    try:
        return ExperienceLevel(raw.strip().lower())
    except ValueError as exc:
        raise typer.BadParameter(
            f"Experience must be one of: {', '.join(EXPERIENCE_VALUES)}"
        ) from exc


def _prompt_skills() -> list[Skill]:
    raw = typer.prompt(f"Skills, comma-separated. Available: {', '.join(SKILL_VALUES)}")
    parts = [part.strip().lower() for part in raw.split(",") if part.strip()]
    if not parts:
        raise typer.BadParameter("Select at least one skill")
    try:
        return [Skill(part) for part in parts]
    except ValueError as exc:
        raise typer.BadParameter(f"Skills must be from: {', '.join(SKILL_VALUES)}") from exc


def _prompt_api_key() -> str | None:
    raw = typer.prompt(
        "Anthropic API key (leave empty to use ANTHROPIC_API_KEY later)",
        default="",
        hide_input=True,
        show_default=False,
    )
    cleaned = raw.strip()
    return cleaned or None


def init_command(
    experience: Annotated[
        ExperienceLevel | None,
        typer.Option(case_sensitive=False, help="Researcher experience level."),
    ] = None,
    skill: Annotated[
        list[Skill] | None,
        typer.Option(
            "--skill", case_sensitive=False, help="Repeatable. From the fixed skill list."
        ),
    ] = None,
    bounty_only: Annotated[
        bool | None,
        typer.Option(
            "--bounty-only/--all-programs",
            help="Only recommend programs that offer bounties.",
        ),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            help="Anthropic API key. Stored in the OS keyring, never in config.toml.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite an existing config.toml without asking."),
    ] = False,
) -> None:
    """Create ~/.config/gehrman/config.toml and store the API key in the keyring."""
    target = config_path()
    if target.is_file() and not force:
        if not typer.confirm(f"Config already exists at {target}. Overwrite?", default=False):
            console.print("Keeping the existing configuration.")
            raise typer.Exit(code=1)

    resolved_experience = experience or _prompt_experience()
    resolved_skills = skill or _prompt_skills()
    if bounty_only is None:
        resolved_bounty_only = typer.confirm(
            "Only recommend programs that offer bounties?",
            default=True,
        )
    else:
        resolved_bounty_only = bounty_only

    try:
        profile = ProfileConfig(
            experience=resolved_experience,
            skills=resolved_skills,
            bounty_only=resolved_bounty_only,
        )
        config = AppConfig(profile=profile)
    except ValidationError as exc:
        raise typer.BadParameter(str(exc)) from exc

    written = save_config(config)
    console.print(f"Wrote configuration to {written}")

    resolved_key = api_key.strip() if api_key else None
    # Empty --api-key should not overwrite; prompt only in interactive mode.
    if resolved_key is None and experience is None and skill is None:
        resolved_key = _prompt_api_key()

    key_status = "not stored (set ANTHROPIC_API_KEY when you run the agent)"
    if resolved_key:
        try:
            store_anthropic_key(resolved_key)
            key_status = "stored in the OS keyring"
        except (SecretStoreError, ValueError):
            key_status = (
                "keyring unavailable — export ANTHROPIC_API_KEY instead; "
                "the key was not written to disk"
            )
            console.print(f"[yellow]{key_status}[/yellow]")

    skills_display = ", ".join(item.value for item in config.profile.skills)
    summary = (
        f"Experience : {config.profile.experience.value}\n"
        f"Skills     : {skills_display}\n"
        f"Bounty only: {config.profile.bounty_only}\n"
        f"API key    : {key_status}\n"
        f"Config     : {written}"
    )
    console.print(Panel(summary, title="Gehrman is ready", border_style="green"))
