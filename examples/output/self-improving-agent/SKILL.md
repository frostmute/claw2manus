---
name: self-improvement
description: 'What it does: Captures learnings, errors, and corrections to enable
  continuous improvement. Use when: (1) A command or operation fails unexpectedly,
  (2) User corrects Claude (''No, that''s wrong...'', ''Actually...''), (3) User requests
  a capability that doesn''t exist, (4) An external API or tool fails, (5) Claude
  realizes its knowledge is outdated or incorrect, (6) A better approach is discovered
  for a recurring task. Also review learnings before major tasks.. When to use it:
  This is a converted skill from ClawHub, review its content for usage instructions.'
metadata: null
---

# Self-Improvement Skill

Log learnings and errors to markdown files for continuous improvement. Coding agents can later process these into fixes, and important learnings get promoted to project memory.

## First-Use Initialisation

Before logging anything, ensure the `.learnings/` directory and files exist in the project or workspace root. If any are missing, create them:

```bash
mkdir -p .learnings
[ -f .learnings/LEARNINGS.md ] || printf "# Learnings\n\nCorrections, insights, and knowledge gaps captured during development.\n\n**Categories**: correction | insight | knowledge_gap | best_practice\n\n---\n" > .learnings/LEARNINGS.md
[ -f .learnings/ERRORS.md ] || printf "# Errors\n\nCommand failures and integration errors.\n\n---\n" > .learnings/ERRORS.md
[ -f .learnings/FEATURE_REQUESTS.md ] || printf "# Feature Requests\n\nCapabilities requested by the user.\n\n---\n" > .learnings/FEATURE_REQUESTS.md
```

Never overwrite existing files. This is a no-op if `.learnings/` is already initialised.

Do not log secrets, tokens, private keys, environment variables, or full source/config files unless the user explicitly asks for that level of detail. Prefer short summaries or redacted excerpts over raw command output or full transcripts.

If you want automatic reminders or setup assistance, use the opt-in hook workflow described in [Hook Integration](#hook-integration).

## Quick Reference

| Situation | Action |
| --- | --- |
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `.learnings/LEARNINGS.md` with category `best_practice` |
| Simplify/Harden recurring patterns | Log/update `.learnings/LEARNINGS.md` with `Source: simplify-and-harden` and a stable `Pattern-Key` |
| Similar to existing entry | Link with **See Also**, consider priority bump |
| Broadly applicable learning | Promote to `soul.md (Manus equivalent for core behavioral patterns)`, `Manus subtask concepts or agent planning phases`, and/or `.github/copilot-instructions.md` |
| Workflow improvements | Promote to `Manus subtask concepts or agent planning phases` (OpenClaw workspace) |
| Tool gotchas | Promote to `TOOLS.md` (OpenClaw workspace) |
| Behavioral patterns | Promote to `SOUL.md` (OpenClaw workspace) |

## OpenClaw Setup (Recommended)

OpenClaw is the primary platform for this skill. It uses workspace-based prompt injection with automatic skill loading.

### Installation

**Via ClawdHub (recommended):**

```bash
Manus: To install skills, place them in `/home/ubuntu/skills/` directory.
```

**Manual:**

```bash
git clone https://github.com/peterskoett/self-improving-agent.git /home/ubuntu/skills/self-improving-agent
```

### Workspace Structure

OpenClaw injects these files into every session:

```
/home/ubuntu/workspace/
├── Manus subtask concepts or agent planning phases
├── SOUL.md
├── TOOLS.md
├── MEMORY.md
├── memory/
│   └── YYYY-MM-DD.md
└── .learnings/
    ├── LEARNINGS.md
    ├── ERRORS.md
    └── FEATURE_REQUESTS.md
```

### Promotion Targets

When learnings prove broadly applicable, promote them to workspace files:

| Learning Type | Promote To | Example |
| --- | --- | --- |
| Behavioral patterns | `SOUL.md` | "Be concise, avoid disclaimers" |
| Workflow improvements | `Manus subtask concepts or agent planning phases` | "Spawn sub-agents for long tasks" |
| Tool gotchas | `TOOLS.md` | "Git push needs auth configured first" |

### Inter-Session Communication

OpenClaw provides tools to share learnings across sessions:

* **Manus: Use `shell` tool with `ps aux` or similar to list processes, or `gws` to list Google Workspace sessions.** — View active/recent sessions
* **Manus: Session history is managed by the agent. Direct access to other session's history is not supported.** — Read another session's transcript
* **Manus: Inter-agent communication is not directly supported via a 'send' tool. Consider using shared files or a message queue.** — Send a learning to another session
* **Manus: To spawn sub-agents, define a new phase in the plan or use parallel processing for homogeneous tasks.** — Spawn a sub-agent for background work

Use these only in trusted environments and only when the user explicitly wants cross-session sharing.

## Generic Setup (Other Agents)

For Claude Code, Codex, Copilot, or other agents, create `.learnings/` in the project or workspace root.

## Logging Format

### Learning Entry

Append to `.learnings/LEARNINGS.md`:

```md
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description

### Details
Full context

### Suggested Action
Specific fix or improvement

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
```

### Error Entry

Append to `.learnings/ERRORS.md`:

```md
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending

### Summary
Brief description

### Error
Actual error message

### Context
- Command attempted
- Input/parameters
- Environment details

### Suggested Fix
Prevention strategy
```

### Feature Request Entry

Append to `.learnings/FEATURE_REQUESTS.md`:

```md
## [REQ-YYYYMMDD-XXX] feature_name

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high
**Status**: pending

### Summary
Brief description

### Use Case
Why needed

### Suggested Implementation
How to implement
```
