# Gehrman

Local CLI assistant that helps a bug bounty researcher choose programs.
Developed as a thesis MVP under a Secure Software Development Life Cycle
(NIST SSDF / SP 800-218A). The research experiment measures how well
layered defenses protect the agent against **indirect prompt injection**.

Gehrman is **passive**: it only reads public program catalogs. It never
scans, probes, or contacts a program's targets.

## Scope

- Platforms: HackerOne and Intigriti, via [arkadiyt/bounty-targets-data](https://github.com/arkadiyt/bounty-targets-data).
- Single user, local Python CLI. No accounts, no web UI.
- Out of scope: Bugcrowd, git-history analysis, ML prediction, scraping.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependencies

## Install

```bash
uv sync --all-groups
uv run gehrman --help
```

## Commands

| Command | Status | Purpose |
| --- | --- | --- |
| `gehrman init` | Milestone 1 | Researcher profile + API key setup |
| `gehrman update` | Later | Download catalogs, store snapshots, score |
| `gehrman chat` | Later | Talk to the agent |

```bash
uv run gehrman init
# or non-interactive (useful in scripts and tests)
uv run gehrman init \
  --experience beginner \
  --skill web --skill api \
  --bounty-only \
  --api-key "$ANTHROPIC_API_KEY"
```

`init` writes `~/.config/gehrman/config.toml` (no secrets) and stores the
Anthropic API key in the OS keyring. If the keyring is unavailable, set
`ANTHROPIC_API_KEY` instead.

Override locations in tests or unusual setups:

- `GEHRMAN_CONFIG_DIR` — directory for `config.toml` (default `~/.config/gehrman`)
- `GEHRMAN_DATA_DIR` — directory for the database and snapshots (default `~/.local/share/gehrman`)

## Security

See [SECURITY.md](SECURITY.md) for trust boundaries.

Defense switches live under `[defenses]` in `config.toml` and default to
on. They are implemented in a later milestone; the flags exist now so
experiments can turn controls on and off without a schema change.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run bandit -r src --severity-level high
uv run pip-audit
```

CI on every push runs ruff, pytest, bandit (fail on high), pip-audit,
gitleaks, and publishes a CycloneDX SBOM.
