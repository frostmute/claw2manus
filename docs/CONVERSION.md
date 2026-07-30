# Conversion Logic Overview

`claw2manus` runs every `SKILL.md` through the same five stages. Each stage
is independently testable and configurable — see
[`CONFIGURATION.md`](CONFIGURATION.md) for the parts you can override.

The staged pipeline:

```text
  input.md
    │
    ▼
  ┌───────────────────────────────┐
  │ 1. Parse YAML frontmatter     │
  └───────────────────────────────┘
    │
    ▼
  ┌───────────────────────────────┐
  │ 2. Transform frontmatter      │  ← _transform_frontmatter()
  └───────────────────────────────┘
    │
    ▼
  ┌───────────────────────────────┐
  │ 3. Apply body rules           │  ← config.yaml::body_rules
  └───────────────────────────────┘
    │
    ▼
  ┌───────────────────────────────┐
  │ 4. Replace tool calls         │  ← config.yaml::tool_replacements
  └───────────────────────────────┘
    │
    ▼
  ┌───────────────────────────────┐
  │ 5. Validate generated output  │  ← ManusSkillValidator
  └───────────────────────────────┘
    │
    ▼
  output.md  +  CONVERSION_REPORT.md
```

## 1. Frontmatter Transformation

The YAML frontmatter is rewritten field by field:

- **`name`** — lowercased, spaces converted to `-`, and aggressively cleaned
  (anything outside `[a-z0-9-]` stripped, collapsed `-` runs) until it
  satisfies `ManusSkillValidator.validate_name` (max 64 chars,
  hyphen-case regex). Both the truncation and the cleanup are logged.
- **`description`** —
  - If absent, a placeholder (`"A skill derived from ClawHub..."`) is
    generated and a "Generated placeholder description" entry is logged.
  - If it doesn't already mention "what it does" and "when to use it",
    the description is wrapped in the standard
    `What it does: <text>. When to use it: ...` template and the change
    is logged.
  - **If it contains `<` or `>`, the description is rejected** (cleared
    to empty) and a "Removed description" entry is logged. The
    validator then flags the missing description so the author can
    rewrite it. We don't silently strip brackets — that would mask
    bugs in upstream skills.
  - Truncated to 1024 chars if over the limit, with `...` appended.
- **Allowed fields only** — `name`, `description`, `license`,
  `allowed-tools`, and `metadata` pass through. Everything else is
  dropped and logged.
- **Empty values dropped** — `null`, `""`, `[]`, and `{}` are removed
  before `yaml.dump` so the output never contains `metadata: null` or
  `metadata: ''` noise.

## 2. Body Rules (`config.yaml::body_rules`)

The body is run through a list of substitution rules from `config.yaml`.
Each rule has:

```yaml
- id: <short-identifier>
  pattern: <python regex>
  replacement: <literal or backref-using string>
  log: <template with {count} and {plural} placeholders>
```

Rules are applied in order; the output of one rule feeds into the next.
Bundled rules include:

| Rule | Pattern | Replacement |
|---|---|---|
| `openclaw-workspace-path` | `~/.openclaw/workspace/` | `/home/ubuntu/workspace/` |
| `openclaw-skills-path` | `~/.openclaw/skills/` | `/home/ubuntu/skills/` |
| `clawdhub-install` | `clawdhub install <name>` | (Manus install hint) |
| `openclaw-hooks-enable` | `openclaw hooks enable` | (Manus note on hook parity) |
| `claude-md-to-soul-md` | `CLAUDE.md` *(word-bounded)* | `soul.md` |
| `agents-md-to-subtasks-md` | `AGENTS.md` *(word-bounded)* | `subtasks.md` |

The `CLAUDE.md` and `AGENTS.md` rules use leading and trailing
look-around guards so that `my-CLAUDE.md`, `CLAUDE.md.bak`, and
`CLAUDE.mdx` are **not** mistaken for the original filename. See the
rules in `claw2manus/config.yaml` for the exact patterns.

To add your own rule, either edit `config.yaml` or call
`SkillConverter.add_rule({...})` programmatically — invalid regexes
raise `ValueError` at insertion time.

## 3. Tool Replacements (`config.yaml::tool_replacements`)

Tool replacements are **name-based, not regex-based**, because they're
paired with the interactive prompt that lets you override per-run:

```yaml
tool_replacements:
  sessions_list: "Manus: Use `shell` tool with `ps aux` or similar..."
  sessions_history: "Manus: Session history is managed by the agent..."
```

When `convert --interactive` is set, every match triggers a prompt
asking what to substitute. Without `--interactive`, the configured
default is used.

## 4. Compatibility Notes (stdio / MCP suggestions)

The `stdio_patterns` list in `config.yaml` is the third config section.
Each entry has a regex, a category, and an MCP suggestion. When the
body matches one of these patterns, a report entry is added that says
"Potential stdio-only tool detected (Category). Use MCP bridge X." No
body rewriting happens — these are advisory only and the conversion
continues.

The default bundled patterns cover script execution, text utilities,
remote access, and database clients.

## 5. Validation

The final Manus `SKILL.md` is fed through `ManusSkillValidator.validate_manus_skill`,
which checks:

- YAML frontmatter is well-formed and non-empty
- `name` matches the hyphen-case regex and is ≤ 64 chars
- `description` is present, non-empty, ≤ 1024 chars, and has no `<` or `>`
- All frontmatter keys are in the allowed set
- The body contains at least one of `## How To Use`, `## Prerequisites`,
  or `## Usage`

Validation errors are appended to the conversion report (the output is
still written). Run `claw2manus validate` separately to validate an
existing Manus skill without converting anything.

## Output Files

For each input skill, the output directory contains:

- `SKILL.md` — converted content
- `CONVERSION_REPORT.md` — list of every transformation applied plus any
  validation errors

If a `CLAUDE.md` file exists alongside the input `SKILL.md`, it is
copied verbatim to `soul.md` in the output (Manus's behavioral-pattern
file).
