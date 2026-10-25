"""Typer application entry point."""

from __future__ import annotations

from typing import Annotated

import typer

from gehrman import __version__
from gehrman.commands.init import init_command

app = typer.Typer(
    name="gehrman",
    help="Local CLI assistant for choosing bug bounty programs. Passive analysis only.",
    no_args_is_help=True,
    add_completion=False,
)
app.command("init")(init_command)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the Gehrman version and exit.",
        ),
    ] = False,
) -> None:
    """Gehrman CLI."""
