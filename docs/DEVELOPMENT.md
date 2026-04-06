# Development Guide

This guide is for contributors who want to extend or modify `claw2manus`.

## Setup

Use `uv` to create a virtual environment and install the package in editable mode with test dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install pytest
```

## Project Structure

*   `claw2manus/cli.py`: The command-line interface logic.
*   `claw2manus/converter.py`: The core `SkillConverter` class.
*   `claw2manus/fetcher.py`: Logic for fetching skills from GitHub and scraping `clawhub.ai`.
*   `claw2manus/validators.py`: The `ManusSkillValidator` for name, description, and formatting checks.
*   `claw2manus/config.yaml`: The mapping definitions for tools and stdio patterns.

## Testing

Run the test suite using `pytest`:

```bash
pytest
```

Tests are located in the `tests/` directory:
*   `tests/test_converter.py`: Tests the `SkillConverter`'s transformation logic.
*   `tests/test_validators.py`: Tests the `ManusSkillValidator`'s rule-based checks.

## Key Libraries Used

*   **PyYAML:** For parsing and generating YAML frontmatter.
*   **BeautifulSoup4:** For scraping `SKILL.md` content from the `clawhub.ai` website.
*   **Requests:** For fetching skills from the GitHub raw API and the GitHub Search API.
*   **Markdown:** (Future use) For advanced parsing of skill body content.
