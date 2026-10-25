from typer.testing import CliRunner

from gehrman.cli import app

runner = CliRunner()


def test_help_lists_init() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "Passive analysis only" in result.output
