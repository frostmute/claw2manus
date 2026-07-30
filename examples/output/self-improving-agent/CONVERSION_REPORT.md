# Conversion Report for self-improving-agent

- Enhanced description for skill 'self-improvement' to include 'what it does' and 'when to use it'.
- Replaced ~/.openclaw/workspace/ with /home/ubuntu/workspace/.
- Replaced ~/.openclaw/skills/ with /home/ubuntu/skills/.
- Replaced OpenClaw tool 'sessions_list' with Manus instruction: Manus: Use `shell` tool with `ps aux` or similar to list processes, or `gws` to list Google Workspace sessions.
- Replaced OpenClaw tool 'sessions_history' with Manus instruction: Manus: Session history is managed by the agent. Direct access to other session's history is not supported.
- Replaced OpenClaw tool 'sessions_send' with Manus instruction: Manus: Inter-agent communication is not directly supported via a 'send' tool. Consider using shared files or a message queue.
- Replaced OpenClaw tool 'sessions_spawn' with Manus instruction: Manus: To spawn sub-agents, define a new phase in the plan or use parallel processing for homogeneous tasks.
- Replaced ClawHub install/hook commands with Manus skill installation instructions.
- Replaced CLAUDE.md with soul.md (Manus equivalent).
- Replaced AGENTS.md with subtasks.md (Manus planning-file equivalent).
- Noted 'OpenClaw workspace' concepts may not have direct 1:1 mapping in Manus; review for manual adaptation.
- 
--- Manus Validation Errors ---
- Body missing a usage-related section (e.g., '## How To Use' or '## Prerequisites').
- -------------------------------
