# Conversion Logic Overview

`claw2manus` automates the transformation of `SKILL.md` files by performing the following operations in sequence:

## 1. Frontmatter Transformation

The YAML frontmatter is cleaned and filtered:
*   **Name:** Hyphen-cased, lowercase, and truncated to 64 characters.
*   **Description:** Enhanced to include "What it does" and "When to use it" if missing. Angle brackets are removed to avoid formatting issues.
*   **Allowed Fields:** Only `name`, `description`, `license`, `allowed-tools`, and `metadata` are retained.

## 2. Body Transformation

The markdown body is modified to replace OpenClaw-specific concepts with Manus platform equivalents:

### Path Replacement
References to the following OpenClaw paths:
*   `~/.openclaw/workspace/` -> `/home/ubuntu/workspace/`
*   `~/.openclaw/skills/` -> `/home/ubuntu/skills/`

### Tool & Command Mapping
*   **OpenClaw Tools:** Matches specific tool names (e.g., `sessions_list`) against the `tool_replacements` section in `config.yaml`.
*   **Installation Commands:** Replaces `clawdhub install` with Manus-compatible skill upload instructions.
*   **Files:** Replaces `CLAUDE.md` with `soul.md` and `AGENTS.md` with Manus subtask planning concepts.

### Stdio-only Tool Detection
The converter identifies potential `stdio`-only tools using regex patterns defined in `config.yaml`. For each match, it adds a report entry with specific suggestions for using the `shell` tool or an MCP bridge.

## 3. Report Generation

A `CONVERSION_REPORT.md` is generated in the output directory, listing:
*   Every transformation performed.
*   Validation errors found in the final Manus skill.
*   Notes on potential manual adaptation requirements (e.g., for complex multi-agent logic).

## 4. Soul.md Generation (Automatic)

If a `CLAUDE.md` file is found in the same directory as the input `SKILL.md`, `claw2manus` automatically copies it as `soul.md` to the output directory. `soul.md` is the Manus platform's file for defining an agent's core behavioral patterns.
