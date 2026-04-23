import re
import yaml
import os
import logging
from claw2manus.validators import ManusSkillValidator

logger = logging.getLogger(__name__)

class SkillConverter:
    def __init__(self, config_path: str = None):
        self.report = []
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> dict:
        default_config = {
            "tool_replacements": {},
            "stdio_patterns": []
        }
        
        if config_path is None:
            # Look for config.yaml in the same directory as this file
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    return config if config else default_config
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return default_config

    def _log_change(self, message: str):
        self.report.append(message)

    def _transform_frontmatter(self, frontmatter: dict) -> dict:
        transformed = {}
        original_name = frontmatter.get("name", "unknown")

        # 1. Name transformation
        name = frontmatter.get("name", "").lower().replace(" ", "-")
        if len(name) > ManusSkillValidator.MAX_NAME_LENGTH:
            name = name[:ManusSkillValidator.MAX_NAME_LENGTH]
            self._log_change(f"Truncated skill name from '{original_name}' to '{name}' (max {ManusSkillValidator.MAX_NAME_LENGTH} chars).")
        if not ManusSkillValidator.validate_name(name):
            # Attempt a more aggressive cleanup if initial conversion fails
            name = re.sub(r'[^a-z0-9-]+', '', name)
            name = re.sub(r'--+', '-', name).strip('-')
            if len(name) > ManusSkillValidator.MAX_NAME_LENGTH:
                name = name[:ManusSkillValidator.MAX_NAME_LENGTH]
            self._log_change(f"Cleaned up skill name from '{original_name}' to '{name}' for Manus compatibility.")
        transformed["name"] = name

        # 2. Description transformation
        description = frontmatter.get("description", "")
        if not description:
            description = f"A skill derived from ClawHub. Original name: {original_name}. Please update this description."
            self._log_change(f"Generated placeholder description for skill '{original_name}' as it was missing.")
        
        # Ensure description includes "what it does AND when to use it"
        if "what it does" not in description.lower() and "when to use it" not in description.lower():
            description = f"What it does: {description}. When to use it: This is a converted skill from ClawHub, review its content for usage instructions."
            self._log_change(f"Enhanced description for skill '{original_name}' to include 'what it does' and 'when to use it'.")

        # Remove angle brackets
        if ">" in description or "<" in description:
            description = description.replace(">", "").replace("<", "")
            self._log_change(f"Removed angle brackets from description for skill '{original_name}' to comply with Manus format.")

        if len(description) > ManusSkillValidator.MAX_DESCRIPTION_LENGTH:
            description = description[:ManusSkillValidator.MAX_DESCRIPTION_LENGTH - 3] + "..."
            self._log_change(f"Truncated description for skill '{original_name}' (max {ManusSkillValidator.MAX_DESCRIPTION_LENGTH} chars).")
        transformed["description"] = description

        # 3. Keep only allowed fields
        for field in ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS:
            if field in frontmatter and field not in transformed:
                transformed[field] = frontmatter[field]
        
        unsupported_fields = set(frontmatter.keys()) - ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS
        if unsupported_fields:
            self._log_change(f"Removed unsupported frontmatter fields for skill '{original_name}': {', '.join(unsupported_fields)}.")

        return transformed

    def _transform_body(self, body: str, interactive: bool = False, on_unresolved_tool=None) -> str:
        transformed_body = body

        # Replace OpenClaw-specific paths
        if "~/.openclaw/workspace/" in transformed_body:
            transformed_body = transformed_body.replace("~/.openclaw/workspace/", "/home/ubuntu/workspace/")
            self._log_change("Replaced ~/.openclaw/workspace/ with /home/ubuntu/workspace/.")
        if "~/.openclaw/skills/" in transformed_body:
            transformed_body = transformed_body.replace("~/.openclaw/skills/", "/home/ubuntu/skills/")
            self._log_change("Replaced ~/.openclaw/skills/ with /home/ubuntu/skills/.")

        # Replace OpenClaw tool references with Manus equivalents or flag as incompatible
        tool_replacements = self.config.get("tool_replacements", {})
        for old_tool, default_instruction in tool_replacements.items():
            if old_tool in transformed_body:
                instruction = default_instruction
                if interactive and on_unresolved_tool:
                    instruction = on_unresolved_tool(old_tool, default_instruction)
                
                transformed_body = transformed_body.replace(old_tool, instruction)
                self._log_change(f"Replaced OpenClaw tool '{old_tool}' with Manus instruction: {instruction}")

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
        stdio_patterns = self.config.get("stdio_patterns", [])
        categories_logged = set()
        for item in stdio_patterns:
            pattern = item.get("pattern")
            category = item.get("category", "General")
            if category in categories_logged:
                continue
            
            if pattern and re.search(pattern, transformed_body, re.IGNORECASE):
                suggestion = item.get("mcp_suggestion", "Check if an MCP bridge is available.")
                self._log_change(f"Potential stdio-only tool detected ({category}) (pattern: {pattern}). {suggestion}")
                categories_logged.add(category)

        # Add compatibility notes where 1:1 mapping isn't possible
        if "OpenClaw workspace" in transformed_body:
            self._log_change("Noted 'OpenClaw workspace' concepts may not have direct 1:1 mapping in Manus; review for manual adaptation.")

        return transformed_body

    def convert(self, clawhub_skill_content: str, interactive: bool = False, on_unresolved_tool=None) -> tuple[str, list[str]]:
        self.report = []
        
        # Robust splitting
        parts = re.split(r'^---\s*$', clawhub_skill_content, maxsplit=2, flags=re.MULTILINE)
        if len(parts) > 2 and parts[0].strip() == "":
            frontmatter_str = parts[1]
            body = parts[2]
        else:
            self._log_change("Input SKILL.md does not have valid YAML frontmatter delimiters.")
            return clawhub_skill_content, self.report 

        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            self._log_change(f"YAML parsing error in frontmatter: {e}")
            return clawhub_skill_content, self.report 

        transformed_frontmatter = self._transform_frontmatter(frontmatter)
        transformed_body = self._transform_body(body, interactive, on_unresolved_tool)

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
