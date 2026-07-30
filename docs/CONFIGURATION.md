# Configuration Guide

`claw2manus` reads `claw2manus/config.yaml` from the installed package by
default. To point it at a different file, pass `config_path` to
`SkillConverter`:

```python
from claw2manus.converter import SkillConverter

converter = SkillConverter(config_path="/path/to/my-config.yaml")
```

The file has three top-level sections. All three are optional.

## 1. `tool_replacements`

Exact-name mappings from OpenClaw tool names to Manus instructions.
These run as plain `str.replace` calls (not regex), so they're a good
fit for known tool names where you don't need to match patterns.

```yaml
tool_replacements:
  sessions_list: "Manus: Use `shell` tool with `ps aux` or similar to list processes, or `gws` to list Google Workspace sessions."
  sessions_history: "Manus: Session history is managed by the agent. Direct access to other session's history is not supported."
  sessions_send: "Manus: Inter-agent communication is not directly supported via a 'send' tool. Consider using shared files or a message queue."
  sessions_spawn: "Manus: To spawn sub-agents, define a new phase in the plan or use parallel processing for homogeneous tasks."
```

When `convert --interactive` is passed, each match triggers a prompt
asking for a custom replacement. Otherwise the value above is used
verbatim.

## 2. `stdio_patterns`

Detection rules for tools that need an MCP bridge or `shell` workaround
on Manus. They don't rewrite the body — they only add entries to
`CONVERSION_REPORT.md`.

```yaml
stdio_patterns:
  - pattern: '(\b(?:python|node|ruby|perl|php|java|go|bash|sh|zsh)\b\s+.*?\.py)'
    category: "Script execution"
    mcp_suggestion: "Check if this can be handled via standard `shell` or if a dedicated MCP bridge is needed."
  - pattern: '(\b(?:cat|less|more|tail|head|grep|awk|sed)\b)'
    category: "Text processing utilities"
    mcp_suggestion: "Standard `shell` tools are usually sufficient."
  - pattern: '(\b(?:ssh|ftp|sftp|scp)\b)'
    category: "Remote access"
    mcp_suggestion: "Consider using an MCP bridge for remote protocol management or using the `shell` tool."
  - pattern: '(\b(?:psql|mysql|sqlite3|mongo|redis-cli)\b)'
    category: "Database clients"
    mcp_suggestion: "Strongly recommend using an MCP server (e.g. `mcp-server-postgres`, `mcp-server-mysql`) for secure and structured database access."
```

Each entry has three fields:

| Field | Required | Purpose |
|---|---|---|
| `pattern` | yes | A Python regex (raw or quoted string). |
| `category` | no | Short label used in the report entry. Defaults to "General". |
| `mcp_suggestion` | no | Specific advice on what to use instead. |

Each category is logged at most once per conversion, even if its pattern
matches the body multiple times.

## 3. `body_rules`

The plugin surface. Each rule is a regex substitution applied to the
body of every SKILL.md, with an optional log template that fires when
at least one match occurred.

```yaml
body_rules:
  - id: claude-md-to-soul-md
    pattern: '(?<![A-Za-z0-9_.-])CLAUDE\.md(?![A-Za-z0-9_.])'
    replacement: soul.md
    log: "Replaced CLAUDE.md with soul.md ({count} occurrence{plural})."

  - id: agents-md-to-subtasks-md
    pattern: '(?<![A-Za-z0-9_.-])AGENTS\.md(?![A-Za-z0-9_.])'
    replacement: subtasks.md
    log: "Replaced AGENTS.md with subtasks.md ({count} occurrence{plural})."
```

### Schema

| Field | Required | Purpose |
|---|---|---|
| `id` | no | Short identifier for debugging. |
| `pattern` | yes | Python regex string. Validated at load time. |
| `replacement` | yes | Literal string passed to `re.sub` — supports backreferences (`\1`, `\g<name>`). |
| `log` | no | Template with `{count}` and `{plural}` placeholders. Emitted only when at least one match occurred. |

### Behavior

- Rules are applied **in order**. The output of one rule is the input
  to the next.
- A rule with an invalid regex is dropped at load time with an error log.
  It does not break the converter.
- A rule that matches zero times is silently passed over — no log entry.
- A rule that matches multiple times logs once with the count, e.g.
  *"Replaced CLAUDE.md with soul.md (3 occurrences)."*

### Adding rules programmatically

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

Invalid regexes raise `ValueError` immediately so plugin authors get
feedback at insertion time, not mid-conversion.

## Customizing Configuration

Three options, in order of preference:

1. **Edit the bundled file.** `claw2manus/config.yaml` is shipped with
   the package. Fork or vendor your own copy and replace it.
2. **Pass a `config_path`** to `SkillConverter(config_path=...)` from
   Python.
3. **Register rules at runtime** via `SkillConverter.add_rule(...)`.

The first wins on simplicity; the second and third avoid forking.

## Validation of config files

`claw2manus` does not currently validate the YAML schema of your config
file. A malformed `body_rules` entry (e.g. missing `replacement`) is
silently skipped at conversion time with a logger warning. Check the
logs or run a single-skill conversion to surface any mistakes.
