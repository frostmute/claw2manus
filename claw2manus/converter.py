import re
import yaml
import os
import logging
from claw2manus.validators import ManusSkillValidator

logger = logging.getLogger(__name__)


def _apply_body_rules(body: str, rules: list, report: list) -> str:
    """Apply a sequence of regex-based substitution rules to a SKILL.md body.

    Each rule is a dict with:
        - id: short identifier (for logs/debugging)
        - pattern: regex string
        - replacement: literal string (with backrefs) used as re.sub replacement
        - log: template added to `report` when at least one replacement is made.
               Supports {count} and {plural} (s if count != 1) placeholders.

    The rules are applied in order and the body is threaded through. Returns
    the transformed body string.
    """
    transformed = body
    for rule in rules:
        if "pattern" not in rule or "replacement" not in rule:
            logger.warning("Skipping malformed rule (missing pattern/replacement): %r", rule)
            continue
        try:
            new_body, count = re.subn(
                rule["pattern"],
                rule["replacement"],
                transformed,
            )
        except re.error as e:
            logger.exception("Invalid regex in rule %r: %s", rule.get("id"), e)
            continue
        if count:
            transformed = new_body
            log_template = rule.get("log")
            if log_template:
                plural = "s" if count != 1 else ""
                report.append(
                    log_template.format(count=count, plural=plural)
                )
    return transformed


class SkillConverter:
    def __init__(self, config_path: str = None):
        self.report = []
        self.config = self._load_config(config_path)
        self._body_rules = self._compile_body_rules(self.config.get("body_rules", []))

    def _load_config(self, config_path: str) -> dict:
        default_config = {
            "tool_replacements": {},
            "stdio_patterns": [],
            "body_rules": [],
        }

        if config_path is None:
            # Look for config.yaml in the same directory as this file
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    if not isinstance(config, dict):
                        # Mock or unexpected return type — fall back to defaults.
                        return default_config
                    # Ensure all expected keys exist
                    for key, default in default_config.items():
                        config.setdefault(key, default)
                    return config
            except Exception as e:
                logger.exception("Error loading config from %s", config_path)

        return default_config

    def _compile_body_rules(self, raw_rules: list) -> list:
        """Pre-validate regexes at load time so any user-supplied rule error
        surfaces immediately rather than mid-conversion."""
        compiled = []
        for rule in raw_rules or []:
            try:
                re.compile(rule.get("pattern", ""))
            except re.error as e:
                logger.error(
                    "Discarding rule %r: invalid regex (%s)", rule.get("id"), e
                )
                continue
            compiled.append(rule)
        return compiled

    def add_rule(self, rule: dict) -> None:
        """Append a single body-transformation rule at runtime. Useful for
        plugins or one-off conversions that need a behavior not in the
        bundled config.yaml.

        The rule must follow the same shape as the YAML entries: at minimum
        a `pattern` and a `replacement`. The regex is validated before being
        added; a ValueError is raised on failure.
        """
        try:
            re.compile(rule.get("pattern", ""))
        except re.error as e:
            raise ValueError(f"Invalid pattern in rule {rule!r}: {e}") from e
        self._body_rules.append(rule)

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
        description = str(description)
        desc_lower = description[:ManusSkillValidator.MAX_DESCRIPTION_LENGTH].lower()
        if "what it does" not in desc_lower and "when to use it" not in desc_lower:
            description = f"What it does: {description}. When to use it: This is a converted skill from ClawHub, review its content for usage instructions."
            self._log_change(f"Enhanced description for skill '{original_name}' to include 'what it does' and 'when to use it'.")

        # Reject angle brackets — they break downstream Markdown rendering and the
        # validator requires their absence. Silent stripping would destroy intent.
        if ">" in description or "<" in description:
            self._log_change(
                f"Removed description for skill '{original_name}': contains angle brackets "
                f"which are not allowed by Manus. Author must rewrite the description."
            )
            description = ""

        if len(description) > ManusSkillValidator.MAX_DESCRIPTION_LENGTH:
            description = description[:ManusSkillValidator.MAX_DESCRIPTION_LENGTH - 3] + "..."
            self._log_change(f"Truncated description for skill '{original_name}' (max {ManusSkillValidator.MAX_DESCRIPTION_LENGTH} chars).")
        transformed["description"] = description

        # 3. Keep only allowed fields, dropping empty/None values so yaml.dump
        # doesn't emit `metadata: null` or similar noise.
        for field in ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS:
            if field in frontmatter and field not in transformed:
                value = frontmatter[field]
                if value in (None, "", [], {}):
                    continue
                transformed[field] = value

        unsupported_fields = set(frontmatter.keys()) - ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS
        if unsupported_fields:
            self._log_change(f"Removed unsupported frontmatter fields for skill '{original_name}': {', '.join(unsupported_fields)}.")

        return transformed

    def _transform_tool_replacements(self, body: str, interactive: bool, on_unresolved_tool) -> str:
        """Replace OpenClaw tool references with their Manus equivalents.

        Tool replacements are intentionally separate from the generic body rule
        list because they support an interactive override — the user can supply
        a custom instruction per tool — and they map an exact tool name (e.g.
        'sessions_list') rather than a regex pattern.
        """
        transformed = body
        tool_replacements = self.config.get("tool_replacements", {})
        for old_tool, default_instruction in tool_replacements.items():
            if old_tool not in transformed:
                continue
            instruction = default_instruction
            if interactive and on_unresolved_tool:
                instruction = on_unresolved_tool(old_tool, default_instruction)
            transformed = transformed.replace(old_tool, instruction)
            self._log_change(f"Replaced OpenClaw tool '{old_tool}' with Manus instruction: {instruction}")
        return transformed

    def _transform_body(self, body: str, interactive: bool = False, on_unresolved_tool=None) -> str:
        # 1. Plugin-driven substitutions from config.yaml (and any runtime-added rules).
        transformed = _apply_body_rules(body, self._body_rules, self.report)

        # 2. Tool replacements (interactive-aware, name-based rather than regex).
        transformed = self._transform_tool_replacements(
            transformed, interactive, on_unresolved_tool
        )

        # 3. Compatibility notes and stdio-pattern detection remain inline because
        # they aren't pure text substitutions — they emit report entries without
        # rewriting the body.
        stdio_patterns = self.config.get("stdio_patterns", [])
        categories_logged = set()
        for item in stdio_patterns:
            pattern = item.get("pattern")
            category = item.get("category", "General")
            if category in categories_logged:
                continue

            if pattern and re.search(pattern, transformed, re.IGNORECASE):
                suggestion = item.get("mcp_suggestion", "Check if an MCP bridge is available.")
                self._log_change(f"Potential stdio-only tool detected ({category}) (pattern: {pattern}). {suggestion}")
                categories_logged.add(category)

        if "OpenClaw workspace" in transformed:
            self._log_change("Noted 'OpenClaw workspace' concepts may not have direct 1:1 mapping in Manus; review for manual adaptation.")

        return transformed

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
