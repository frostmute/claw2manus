# claw2manus

`claw2manus` is an open-source Python tool designed to bridge the gap between ClawHub (OpenClaw) skills and Manus-compatible skills. It automates the conversion of `SKILL.md` files, adapting their structure, content, and references to align with Manus platform requirements.

## Why claw2manus?

ClawHub boasts a rich ecosystem of over 8000 skills, offering a vast repository of AI capabilities. However, direct compatibility with Manus is limited due to differing `SKILL.md` formats, platform-specific references, and tool integrations. `claw2manus` addresses this by providing an automated, reliable way to transform ClawHub skills into a format readily usable within the Manus environment, unlocking a wealth of pre-built functionalities for Manus users.

## Installation

To install `claw2manus`, clone the repository and install it using `pip`:

```bash
git clone https://github.com/manus-ai/claw2manus.git
cd claw2manus
sudo pip3 install -e .
```

This will install the `claw2manus` command-line tool and its dependencies.

## Usage

`claw2manus` provides a command-line interface with three main commands: `convert`, `fetch-and-convert`, and `validate`.

### Convert from a Local File

Convert a `SKILL.md` file from your local filesystem to a Manus-compatible format.

```bash
claw2manus convert ./path/to/ClawHub/SKILL.md --output ./output/directory/
```

**Example:**

```bash
claw2manus convert examples/input/pwnclaw-security-scan/SKILL.md --output examples/output/pwnclaw-security-scan/
```

To see the conversion report and the converted skill content without saving it to a file (dry run):

```bash
claw2manus convert ./path/to/ClawHub/SKILL.md --dry-run
```

### Fetch from ClawHub and Convert

Fetch a skill directly from ClawHub (or its GitHub repository) and convert it.

You can specify the skill by its name (e.g., `pwnclaw-security-scan`) or a full GitHub raw URL.

```bash
claw2manus fetch-and-convert pwnclaw-security-scan --output ./output/directory/
```

**Example (by name):**

```bash
claw2manus fetch-and-convert self-improving-agent --output examples/output/self-improving-agent/
```

**Example (by URL):**

```bash
claw2manus fetch-and-convert https://raw.githubusercontent.com/openclaw/skills/main/skills/peterskoett/self-improving-agent/SKILL.md --output examples/output/self-improving-agent/
```

### Validate an Existing Manus Skill

Validate a `SKILL.md` file against Manus skill requirements.

```bash
claw2manus validate ./path/to/Manus/SKILL.md
```

**Example:**

```bash
claw2manus validate examples/output/pwnclaw-security-scan/SKILL.md
```

## How the Conversion Works

The `claw2manus` converter performs several key transformations:

1.  **Frontmatter Transformation:**
    *   **Name:** Ensures the skill name is hyphen-cased, lowercase, and within a maximum of 64 characters. Aggressive cleanup is applied if the initial conversion fails.
    *   **Description:** Rewrites the description to explicitly include 
    "what it does AND when to use it", limits it to 1024 characters, and removes any angle brackets.
    *   **Field Filtering:** Removes any unsupported frontmatter fields, retaining only `name`, `description`, `license`, `allowed-tools`, and `metadata`.

2.  **Body Transformation:**
    *   **Path Replacement:** Replaces OpenClaw-specific paths (e.g., `~/.openclaw/workspace/`, `~/.openclaw/skills/`) with Manus equivalents (e.g., `/home/ubuntu/workspace/`, `/home/ubuntu/skills/`).
    *   **Tool Mapping:** Replaces references to OpenClaw tools (e.g., `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`) with Manus-compatible instructions or flags them as incompatible, providing guidance for manual adaptation.
    *   **Installation Commands:** Replaces `clawdhub install` and `openclaw hooks enable` commands with instructions relevant to Manus skill installation.
    *   **File References:** Replaces references to `CLAUDE.md` with `soul.md` and `AGENTS.md` with Manus subtask concepts.
    *   **Compatibility Notes:** Adds notes where direct 1:1 mapping is not possible, guiding the user on potential manual steps.

3.  **Conversion Report Generation:**
    *   Generates a detailed report listing all changes made during the conversion process and any manual steps that might be required for full compatibility.

4.  **Validation:**
    *   The converted skill is validated against Manus requirements for name format, description length, and allowed frontmatter fields.

## Known Limitations

*   **Scraping ClawHub.ai:** Direct scraping of `clawhub.ai` is not fully robust and may break if the website structure changes. Fetching from GitHub raw URLs is more reliable.
*   **stdio-only Tools:** Detection of `stdio`-only tools is heuristic and may not be exhaustive. Skills relying heavily on interactive `stdio` tools might require further manual adaptation or MCP bridging for full Manus compatibility.
*   **Complex Integrations:** Skills with deep, custom integrations with OpenClaw-specific APIs or complex multi-agent communication patterns might require significant manual refactoring.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
