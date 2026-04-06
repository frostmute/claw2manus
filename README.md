# claw2manus

`claw2manus` is an open-source Python tool designed to bridge the gap between ClawHub (OpenClaw) skills and Meta's Manus-compatible skills. It automates the conversion of `SKILL.md` files, adapting their structure, content, and references to align with Manus platform requirements.

## Features

*   **Batch Conversion:** Convert entire directories of ClawHub skills with `convert-all`.
*   **Automatic `soul.md` Generation:** Automatically converts `CLAUDE.md` to `soul.md` (the Manus behavioral pattern file).
*   **Interactive Mode:** Manually resolve tool mappings during conversion using the `--interactive` flag.
*   **Configuration-Driven Mapping:** Customize tool replacements and `stdio` patterns via `config.yaml`.
*   **Smart Fetching:** Fetch skills directly from ClawHub/GitHub by name with automatic author discovery using the GitHub Search API.
*   **Robust Scraping:** Fallback to scraping `clawhub.ai` when skills are not found on GitHub.
*   **Detailed Reporting:** Generates a `CONVERSION_REPORT.md` for every conversion, listing changes and suggestions for manual adaptation.
*   **Validation:** Built-in validator for Manus skill standards (naming, description length, and required sections).

## Installation

To install `claw2manus`, clone the repository and install it using `uv` (recommended) or `pip`:

```bash
git clone https://github.com/manus-ai/claw2manus.git
cd claw2manus
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Usage

`claw2manus` provides a command-line interface with four main commands: `convert`, `convert-all`, `fetch-and-convert`, and `validate`.

### Convert a Local File

Convert a `SKILL.md` file to a Manus-compatible format.

```bash
claw2manus convert ./path/to/ClawHub/SKILL.md --output ./output/directory/
```

To enable interactive mode for tool mapping:

```bash
claw2manus convert ./path/to/ClawHub/SKILL.md --interactive
```

### Batch Convert a Directory

Convert all `SKILL.md` files found in a directory recursively.

```bash
claw2manus convert-all ./skills/ --output ./manus-skills/
```

### Fetch from ClawHub and Convert

Fetch a skill by its name or full GitHub raw URL.

```bash
claw2manus fetch-and-convert pwnclaw-security-scan --output ./output/
```

The tool will automatically attempt to discover the correct author using the GitHub API.

### Validate an Existing Manus Skill

Validate a `SKILL.md` file against Manus skill requirements.

```bash
claw2manus validate ./path/to/Manus/SKILL.md
```

## Documentation

For more detailed information, see the following guides:

*   [Conversion Logic Overview](docs/CONVERSION.md)
*   [Configuration Guide](docs/CONFIGURATION.md)
*   [Development Guide](docs/DEVELOPMENT.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
