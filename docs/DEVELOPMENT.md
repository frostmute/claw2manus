---
layout: default
title: Development
nav_order: 4
---

# Development Guide

For contributors extending or modifying `claw2manus`.

## Setup

We recommend [`uv`](https://docs.astral.sh/uv/) — it's fast, handles
the venv and dependencies in one go, and is what `claw2manus`'s own CI
uses. `pip`/`venv` works equally well.

```bash
# With uv
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"

# With pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Project Structure

```text
claw2manus/
├── setup.py                  ← PyPI metadata + entry point
├── pyproject.toml            ← (optional) tool configuration
├── .pre-commit-config.yaml   ← ruff + hygiene hooks
├── .github/workflows/
│   └── test.yml              ← CI: pytest on Python 3.10 / 3.11 / 3.12
├── claw2manus/               ← the package
│   ├── __init__.py
│   ├── cli.py                ← argparse, _safe_dir_name, _print_diff
│   ├── converter.py          ← SkillConverter, add_rule(), body-rules engine
│   ├── fetcher.py            ← GitHub content + Search API, clawhub.ai scrape
│   ├── validators.py         ← ManusSkillValidator
│   └── config.yaml           ← bundled rule + tool-replacement defaults
├── docs/
│   ├── CONVERSION.md         ← what each stage of the converter does
│   ├── CONFIGURATION.md      ← config.yaml schema and examples
│   └── DEVELOPMENT.md        ← this file
├── examples/
│   ├── input/                ← sample input skills
│   └── output/               ← expected converted output + reports
└── tests/
    ├── conftest.py           ← real-yaml-when-available policy
    ├── fixtures/
    │   └── integration_repo/ ← three-skill fixture for end-to-end tests
    ├── test_cli.py           ← CLI helpers, --diff mode, output paths
    ├── test_converter.py     ← converter + add_rule() + body rules
    ├── test_fetcher.py       ← URL escaping, GITHUB_TOKEN, scrape fallback
    ├── test_integration.py   ← end-to-end against the fixture repo
    └── test_validators.py    ← ManusSkillValidator unit tests
```

## Testing

The test suite uses `pytest`. There's a fallback policy in `conftest.py`:
when PyYAML / requests / bs4 / markdown aren't installed, it injects
lightweight mocks so the test files still import. With the `[test]`
extra installed (which is what `pip install -e ".[test]"` does), the
real packages are used.

```bash
# Full suite
pytest

# Verbose, one line per test
pytest -v

# Single file
pytest tests/test_converter.py

# Single test (by substring of test name)
pytest -k test_safe_dir_name

# With coverage (install coverage first)
pytest --cov=claw2manus
```

The integration suite (`tests/test_integration.py`) skips automatically
when PyYAML isn't installed. With the standard install, all 92 tests
run in under a second.

## Code style

`claw2manus` uses `ruff` for linting and formatting — see
`.pre-commit-config.yaml`. Settings are in `pyproject.toml` (or default
ruff ones if you don't have a `pyproject.toml` yet).

```bash
# Format and lint
ruff format .
ruff check --fix .

# Just check, no fixes
ruff check .
```

Pre-commit is configured to run `ruff` and a basic hygiene suite on
every commit. Enable it locally:

```bash
pip install pre-commit
pre-commit install
```

## Adding a new feature

The fastest path is usually:

1. Decide which module owns it.
   - CLI surface → `claw2manus/cli.py`
   - Conversion rule → `claw2manus/converter.py` and a config entry
   - Network behavior → `claw2manus/fetcher.py`
   - Manuscript rule → `claw2manus/validators.py`

2. Add tests under `tests/test_*.py`. For end-to-end behavior, add a
   fixture under `tests/fixtures/integration_repo/`.

3. If you added a new config key, document it in
   `docs/CONFIGURATION.md`.

4. If the README's command table changed, update `README.md`.

5. Run `pytest` and `ruff check`. Push a PR.

## Adding a new body rule

The cleanest way is to extend the bundled `claw2manus/config.yaml`:

```yaml
body_rules:
  - id: my-rule
    pattern: '\\bfoo\\b'
    replacement: 'bar'
    log: "Replaced foo with bar ({count} occurrence{plural})."
```

Add a test in `tests/test_converter.py` exercising the rule through
`SkillConverter.convert()` (use the existing tests as templates), and
run `pytest`.

## Releases

`claw2manus` is not yet on PyPI. To cut a release:

1. Bump the version in `setup.py`.
2. Update `CHANGELOG.md` (when one exists).
3. Tag and push: `git tag vX.Y.Z && git push --tags`.
4. Build and publish with `python -m build && twine upload dist/*`
   (after configuring `~/.pypirc`).

## CI

GitHub Actions runs on every push to `main` and on pull requests
(`.github/workflows/test.yml`):

- **Python matrix**: 3.10, 3.11, 3.12
- **Steps**: setup, install (`pip install -e ".[test]"`), `pytest -v`
- **Caching**: `pip` cache keyed on `pyproject.toml`/`setup.py`

If a CI run fails, push a fix and the workflow will re-run.

## Key Libraries

- **[PyYAML](https://pyyaml.org/)** — frontmatter parsing and emission.
- **[requests](https://requests.readthedocs.io/)** — GitHub content fetch
  and Search API.
- **[beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)** —
  scraping fallback for `clawhub.ai` when GitHub lookup fails.
- **[markdown](https://python-markdown.github.io/)** — declared but not
  yet used; reserved for future body parsing work.
