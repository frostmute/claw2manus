import re
import yaml
from claw2manus.validators import ManusSkillValidator

class SkillConverter:
    def __init__(self):
        self.report = []

    def _log_change(self, message: str):
        self.report.append(message)

    def _transform_frontmatter(self, frontmatter: dict) -> dict:
        transformed = {}
        original_name = frontmatter.get("name", "unknown")

        # 1. Name transformation
        name = frontmatter.get("name", "").lower().replace(" ", "-")
        if len(name) > ManusSkillValidator.MAX_NAME_LENGTH:
            name = name[:ManusSkillValidator.MAX_NAME_LENGTH]
            self._log_change(f"Truncated skill name from \'{original_name}\' to \'{name}\' (max {ManusSkillValidator.MAX_NAME_LENGTH} chars).")
        if not ManusSkillValidator.validate_name(name):
            # Attempt a more aggressive cleanup if initial conversion fails
            name = re.sub(r'[^a-z0-9-]+', '', name)
            name = re.sub(r'--+', '-', name).strip('-')
            if len(name) > ManusSkillValidator.MAX_NAME_LENGTH:
                name = name[:ManusSkillValidator.MAX_NAME_LENGTH]
            self._log_change(f"Cleaned up skill name from \'{original_name}\' to \'{name}\' for Manus compatibility.")
        transformed["name"] = name

        # 2. Description transformation
        description = frontmatter.get("description", "")
        if not description:
            description = f"A skill derived from ClawHub. Original name: {original_name}. Please update this description."
            self._log_change(f"Generated placeholder description for skill \'{original_name}\' as it was missing.")
        
        # Ensure description includes "what it does AND when to use it"
        if "what it does" not in description.lower() and "when to use it" not in description.lower():
            description = f"What it does: {description}. When to use it: This is a converted skill from ClawHub, review its content for usage instructions."
            self._log_change(f"Enhanced description for skill \'{original_name}\' to include 'what it does' and 'when to use it'.")

        # Remove angle brackets
        if ">" in description or "<" in description:
            description = description.replace(">", "").replace("<", "")
            self._log_change(f"Removed angle brackets from description for skill \'{original_name}\' to comply with Manus format.")

        if len(description) > ManusSkillValidator.MAX_DESCRIPTION_LENGTH:
            description = description[:ManusSkillValidator.MAX_DESCRIPTION_LENGTH - 3] + "..."
            self._log_change(f"Truncated description for skill \'{original_name}\' (max {ManusSkillValidator.MAX_DESCRIPTION_LENGTH} chars).")
        transformed["description"] = description

        # 3. Keep only allowed fields
        for field in ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS:
            if field in frontmatter and field not in transformed:
                transformed[field] = frontmatter[field]
        
        unsupported_fields = set(frontmatter.keys()) - ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS
        if unsupported_fields:
            self._log_change(f"Removed unsupported frontmatter fields for skill \'{original_name}\': {', '.join(unsupported_fields)}.")

        return transformed

    def _transform_body(self, body: str) -> str:
        transformed_body = body

        # Replace OpenClaw-specific paths
        transformed_body = re.sub(r"~/.openclaw/workspace/", "/home/ubuntu/workspace/", transformed_body)
        if "~/.openclaw/workspace/" in body:
            self._log_change("Replaced ~/.openclaw/workspace/ with /home/ubuntu/workspace/.")
        transformed_body = re.sub(r"~/.openclaw/skills/", "/home/ubuntu/skills/", transformed_body)
        if "~/.openclaw/skills/" in body:
            self._log_change("Replaced ~/.openclaw/skills/ with /home/ubuntu/skills/.")

        # Replace OpenClaw tool references with Manus equivalents or flag as incompatible
        tool_replacements = {
            "sessions_list": "Manus: Use `shell` tool with `ps aux` or similar to list processes, or `gws` to list Google Workspace sessions.",
            "sessions_history": "Manus: Session history is managed by the agent. Direct access to other session's history is not supported.",
            "sessions_send": "Manus: Inter-agent communication is not directly supported via a 'send' tool. Consider using shared files or a message queue.",
            "sessions_spawn": "Manus: To spawn sub-agents, define a new phase in the plan or use parallel processing for homogeneous tasks."
        }
        for old_tool, new_instruction in tool_replacements.items():
            if old_tool in transformed_body:
                transformed_body = transformed_body.replace(old_tool, new_instruction)
                self._log_change(f"Replaced OpenClaw tool \'{old_tool}\' with Manus instruction: {new_instruction}")

        # Replace clawdhub/openclaw install commands with Manus skill upload instructions
        if "clawdhub install" in transformed_body or "openclaw hooks enable" in transformed_body:
            transformed_body = re.sub(r"clawdhub install [a-zA-Z0-9-]+", "Manus: To install skills, place them in `/home/ubuntu/skills/` directory.", transformed_body)
            transformed_body = re.sub(r"openclaw hooks enable", "Manus: Hooks are not directly supported. Implement similar functionality using file watchers or scheduled tasks.", transformed_body)
            self._log_change("Replaced ClawHub install/hook commands with Manus skill installation instructions.")

        # Replace references to CLAUDE.md with soul.md where appropriate
        if "CLAUDE.md" in transformed_body:
            transformed_body = transformed_body.replace("CLAUDE.md", "soul.md (Manus equivalent for core behavioral patterns)")
            self._log_change("Replaced CLAUDE.md with soul.md (Manus equivalent).")

        # Replace AGENTS.md references with Manus subtask concepts
        if "AGENTS.md" in transformed_body:
            transformed_body = transformed_body.replace("AGENTS.md", "Manus subtask concepts or agent planning phases")
            self._log_change("Replaced AGENTS.md with Manus subtask concepts.")

        # Flag any stdio-only tools that would need MCP bridging
        # This is a heuristic, as we don't know all stdio-only tools. We'll look for common patterns.
        stdio_patterns = [
            r"((?:python|node|ruby|perl|php|java|go|bash|sh|zsh)\s+.*?\.py)", # Script execution
            r"((?:cat|less|more|tail|head|grep|awk|sed))", # Text processing utilities
            r"((?:ssh|ftp|sftp|scp))" # Remote access
        ]
        for pattern in stdio_patterns:
            if re.search(pattern, transformed_body, re.IGNORECASE):
                self._log_change(f"Potential stdio-only tool detected (pattern: {pattern}). May require MCP bridging for full Manus compatibility.")
                break # Log only once per body for this category

        # Add compatibility notes where 1:1 mapping isn't possible
        if "OpenClaw workspace" in transformed_body:
            self._log_change("Noted 'OpenClaw workspace' concepts may not have direct 1:1 mapping in Manus; review for manual adaptation.")

        return transformed_body

    def convert(self, clawhub_skill_content: str) -> tuple[str, list[str]]:
        self.report = []
        
        parts = clawhub_skill_content.split("---\n", 2)
        if len(parts) < 3:
            self._log_change("Input SKILL.md does not have valid YAML frontmatter delimiters.")
            return clawhub_skill_content, self.report # Return original content if parsing fails

        frontmatter_str = parts[1]
        body = parts[2]

        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            self._log_change(f"YAML parsing error in frontmatter: {e}")
            return clawhub_skill_content, self.report # Return original content if parsing fails

        transformed_frontmatter = self._transform_frontmatter(frontmatter)
        transformed_body = self._transform_body(body)

        # Reconstruct the Manus SKILL.md
        manus_skill_content = "---\n" + \
                              yaml.dump(transformed_frontmatter, sort_keys=False, default_flow_style=False) + \
                              "---\n" + \
                              transformed_body
        
        # Validate the generated Manus skill
        validation_errors = ManusSkillValidator.validate_manus_skill(manus_skill_content)
        if validation_errors:
            self._log_change("\n--- Manus Validation Errors ---")
            for error in validation_errors:
                self._log_change(error)
            self._log_change("-------------------------------")

        return manus_skill_content, self.report


