<div align="center">

# claw2manus

**Convert [ClawHub](https://clawhub.ai) skills into [Manus](https://manus.im)-compatible skills.**

A small, fast, fully-tested Python CLI that translates OpenClaw `SKILL.md` files to
Manus format in one pass — frontmatter cleanup, body rewriting, GitHub fetching,
and a change report you can actually audit.

[![CI](https://img.shields.io/github/actions/workflow/status/frostmute/claw2manus/test.yml?branch=main&label=tests&style=flat-square)](https://github.com/frostmute/claw2manus/actions)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-92%20passing-brightgreen?style=flat-square)](tests/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-yellow?style=flat-square)](.pre-commit-config.yaml)

<img src="docs/hero.png" alt="claw2manus — a claw cradling the moon over a cascade of data" width="520" />

</div>

---

## What this does

ClawHub (the OpenClaw skill registry) and Manus use the same idea — a `SKILL.md`
file with YAML frontmatter and markdown body — but they don't agree on the names,
allowed fields, or filesystem paths. `claw2manus` is the translator.

```text
   ClawHub SKILL.md                              Manus SKILL.md
   ─────────────────                            ────────────────
   name: Test Skill                              name: test-skill
   description: "A test skill."                 description: "What it does: A test skill.
                                                              When to use it: This is a converted
                                                              skill from ClawHub, ..."
                                                 metadata: null          ← dropped
   # Body                                        # Body
   ~/.openclaw/workspace/test  →  /home/ubuntu/workspace/test
   sessions_list                →  Manus: Use `shell` tool with `ps aux` ...
   See CLAUDE.md                →  See soul.md
   See AGENTS.md                →  See subtasks.md
```

Every change is logged in a `CONVERSION_REPORT.md` next to the output so you
can review what happened and revert what you didn't want.

## Why use it

- **One command, one directory.** `convert-all` walks a tree of skills, emits
  clean Manus output, and never collides on names — even when two skills
  share an author.
- **Auditable.** Every body substitution is a configurable rule in
  `config.yaml`. Add your own without touching code.
- **Honest about what it can't do.** No silent `CLAUDE.md` → three-paragraph
  prose rewrites — your references stay as filenames. No silent bracket
  stripping that masks bugs — descriptions with `<` or `>` are rejected so
  the validator can flag them.
- **Respects auth.** Set `GITHUB_TOKEN` and you'll get the 5,000 req/hr
  GitHub limit instead of 60. Anonymous use still works.

## Features

| Capability | What you get |
|---|---|
| **Batch conversion** | `convert-all` walks a directory tree and translates every `SKILL.md` it finds. |
| **Skill fetching** | `fetch-and-convert` resolves a name through GitHub, with a `clawhub.ai` scraping fallback for skills not on GitHub. |
| **Plugin rules** | Body transformations live in `config.yaml` as a list. Add yours with `SkillConverter.add_rule({...})`. |
| **Interactive mode** | `--interactive` lets you override tool replacements per-run. |
| **Dry-run + diff** | `--dry-run` prints the full output; `--diff` shows a unified diff between input and result. |
| **Validation** | Built-in `validate` command checks naming, length, allowed fields, and required sections. |
| **Conversion report** | Every run emits a `CONVERSION_REPORT.md` next to the converted `SKILL.md`. |
| **Path safety** | Output directory names are sanitized; `..` traversal is rejected. |
| **Tested** | 92 tests, including end-to-end fixtures in `tests/fixtures/`. |

## Install

```bash
# Recommended: uv
git clone https://github.com/frostmute/claw2manus.git
cd claw2manus
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
```

Or with plain `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

System Python works too, but a venv keeps `claw2manus` from polluting your
site-packages.

## Quickstart

### Convert a local skill

```bash
claw2manus convert ./path/to/SKILL.md --output ./out/
```

A `CONVERSION_REPORT.md` lands in `./out/<skill-name>/` next to the
converted `SKILL.md`.

### See what would change before committing

```bash
claw2manus convert ./path/to/SKILL.md --dry-run --diff
```

`--dry-run` shows the full output. `--diff` shows a unified diff instead of
(or in addition to) the full output. Combine them to review a change without
writing anything to disk.

### Convert a whole directory

```bash
claw2manus convert-all ./skills/ --output ./manus-skills/
```

Nested layouts like `skills/<author>/<skill>/SKILL.md` are disambiguated
automatically — the output gets `manus-skills/<author>-<skill>/` directories
that won't collide.

### Pull from ClawHub by name

```bash
# Resolves through GitHub's index, with author discovery via Search API
claw2manus fetch-and-convert pwnclaw-security-scan --output ./out/

# Or with a direct URL — GitHub `blob/...` or raw URLs both work
claw2manus fetch-and-convert \
  https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/skills/tweetclaw/SKILL.md \
  --output ./out/
```

For high-volume use, set a GitHub token to lift the rate limit:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
claw2manus fetch-and-convert ...
```

### Validate an existing Manus skill

```bash
claw2manus validate ./path/to/Manus/SKILL.md
# or point it at a directory containing SKILL.md
claw2manus validate ./my-manus-skill/
```

## Commands

| Command | Purpose |
|---|---|
| `claw2manus convert <path>` | Convert one `SKILL.md`. Flags: `--output`, `--dry-run`, `--diff`, `--interactive`. |
| `claw2manus convert-all <dir>` | Convert every `SKILL.md` under `<dir>` recursively. Flags: `--output`, `--interactive`. |
| `claw2manus fetch-and-convert <name\|url>` | Resolve a name or URL through GitHub / ClawHub and convert. Flags: `--output`, `--interactive`. |
| `claw2manus validate <path>` | Validate an existing `SKILL.md` against Manus rules. |

Global exit semantics:

| Code | When |
|---|---|
| `0` | Conversion succeeded, validation clean (or no validation requested) |
| `1` | Validation reported errors, or a fatal conversion failure occurred |
| `2` | Invalid CLI arguments |

## Configuration

`claw2manus` reads `claw2manus/config.yaml` from the installed package by default.
You can override it by passing `config_path` to `SkillConverter()` programmatically.

The config file has three sections. See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)
for the full schema and walked examples.

```yaml
# 1. Exact-name tool replacements (OpenClaw → Manus instruction text).
tool_replacements:
  sessions_list: "Manus: Use `shell` tool with `ps aux` ..."

# 2. Detection patterns for stdio-only tools that may need an MCP bridge.
stdio_patterns:
  - pattern: '(\b(?:psql|mysql|sqlite3)\b)'
    category: "Database clients"
    mcp_suggestion: "Use an MCP server (e.g. mcp-server-postgres)."

# 3. Body substitution rules — regex + replacement + log template.
body_rules:
  - id: claude-md-to-soul-md
    pattern: '(?<![A-Za-z0-9_.-])CLAUDE\.md(?![A-Za-z0-9_.])'
    replacement: soul.md
    log: "Replaced CLAUDE.md with soul.md ({count} occurrence{plural})."
```

To add rules programmatically:

```python
from claw2manus.converter import SkillConverter

converter = SkillConverter()
converter.add_rule({
    "id": "my-custom-rule",
    "pattern": r"foo",
    "replacement": "bar",
    "log": "Replaced foo with bar ({count} occurrence{plural}).",
})
```

Invalid regexes raise `ValueError` at insertion time, so plugin authors get
immediate feedback.

## Project layout

```text
claw2manus/
├── README.md                  ← you are here
├── LICENSE
├── setup.py                   ← PyPI metadata + entry point
├── .pre-commit-config.yaml    ← ruff + hygiene hooks
├── .github/
│   └── workflows/test.yml     ← CI on Python 3.10 / 3.11 / 3.12
├── claw2manus/
│   ├── __init__.py
│   ├── cli.py                 ← argparse, _safe_dir_name, --diff
│   ├── converter.py           ← SkillConverter, add_rule(), body rules engine
│   ├── fetcher.py             ← GitHub content + Search, clawhub.ai scraping
│   ├── validators.py          ← ManusSkillValidator
│   └── config.yaml            ← bundled rule + tool-replacement defaults
├── docs/
│   ├── CONVERSION.md          ← what the converter actually does
│   ├── CONFIGURATION.md       ← config.yaml schema
│   └── DEVELOPMENT.md         ← dev workflow + project layout
├── examples/
│   ├── input/                 ← sample input skills
│   └── output/                ← expected converted output + reports
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   └── integration_repo/  ← three-skill fixture for end-to-end tests
    ├── test_cli.py
    ├── test_converter.py
    ├── test_fetcher.py
    ├── test_integration.py    ← end-to-end against the fixture repo
    └── test_validators.py
```

## Develop

```bash
# Install with test extras
uv pip install -e ".[test]"

# Run the test suite
pytest

# Run a single test by name
pytest -k test_safe_dir_name

# Format & lint
ruff format .
ruff check --fix .
```

Pre-commit hooks are configured — `pre-commit install` will catch lint and
whitespace issues before they hit CI. CI itself runs on Python 3.10, 3.11,
and 3.12 via `.github/workflows/test.yml`.

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for the full contributor guide.

## Documentation index

- [Conversion Logic](docs/CONVERSION.md) — what each stage of the converter does
- [Configuration Guide](docs/CONFIGURATION.md) — `config.yaml` schema and examples
- [Development Guide](docs/DEVELOPMENT.md) — setup, project layout, testing
- [Changelog](CHANGELOG.md) — version history

## Security

The fetcher takes a hostile-input stance:

- Path segments in GitHub URLs are URL-encoded, including `.` (to block
  `..` traversal).
- `fetch-and-convert` runs derived skill names through `_safe_dir_name`
  before treating them as filesystem paths.
- Output directory names are validated against `[A-Za-z0-9._-]`; anything
  outside that becomes `converted-skill`.

If you discover a path-traversal or injection issue, please open a
security-focused issue or email `frostmute@users.noreply.github.com`.

## Contributing

PRs welcome. Use `pre-commit` and run `pytest` before pushing. Tests for new
behavior go in the relevant `tests/test_*.py` file; end-to-end behavior
should add a fixture under `tests/fixtures/`.

## Roadmap

- **`diff` improvements** — side-by-side rendering for visual review
- **Plugin discovery** — `SkillConverter.plugins` hook for users to register
  rules from external packages
- **Schema versioning** — handle v1 vs v2 Manus skill frontmatter
- **More `MANIFEST.in`-friendly packaging** — `pyproject.toml` migration

## License

[MIT](LICENSE) — see the file for full text.

## Acknowledgments

- The [OpenClaw](https://clawhub.ai) project for the source skill format.
- [Manus](https://manus.im) for the destination format.
- Contributors and issue reporters.
