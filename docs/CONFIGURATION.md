# Configuration Guide

`claw2manus` uses a `config.yaml` file to define how ClawHub-specific elements are mapped to the Manus platform. This file is located at `claw2manus/config.yaml` within the package.

## Tool Replacements

The `tool_replacements` section maps OpenClaw-specific tool names to Manus-compatible instructions.

```yaml
tool_replacements:
  sessions_list: "Manus: Use `shell` tool with `ps aux`..."
  sessions_send: "Manus: Inter-agent communication is not directly supported..."
```

When a tool name matches a key in this section, it is replaced with the corresponding value. If you use the `--interactive` flag, you will be prompted to provide a custom replacement for each match.

## Stdio Patterns & MCP Suggestions

The `stdio_patterns` section is used to detect tools that rely on standard I/O and might require an MCP (Model Context Protocol) bridge for full functionality in Manus.

```yaml
stdio_patterns:
  - pattern: '(\b(?:python|node|ruby|...)\b\s+.*?\.py)'
    category: "Script execution"
    mcp_suggestion: "Check if this can be handled via standard `shell`..."
  - pattern: '(\b(?:psql|mysql|sqlite3)\b)'
    category: "Database clients"
    mcp_suggestion: "Strongly recommend using an MCP server (e.g., `mcp-server-postgres`)..."
```

### Fields:
*   **pattern:** A regular expression used to match tool usage in the body of the `SKILL.md`.
*   **category:** A human-readable label for the type of tool detected.
*   **mcp_suggestion:** Specific advice on which MCP server or alternative tool could be used to bridge the functionality.

## Customizing Configuration

You can modify the default `config.yaml` included with the package, or you can point the `SkillConverter` to a custom YAML file by passing the `config_path` argument during initialization.
