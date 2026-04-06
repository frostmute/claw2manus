import re
import yaml

class ManusSkillValidator:
    MAX_NAME_LENGTH = 64
    MAX_DESCRIPTION_LENGTH = 1024
    ALLOWED_FRONTMATTER_FIELDS = {'name', 'description', 'license', 'allowed-tools', 'metadata'}

    @staticmethod
    def validate_name(name: str) -> bool:
        """Validates if the skill name is hyphen-case, lowercase, and within max length."""
        if not isinstance(name, str):
            return False
        if not re.fullmatch(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', name):
            return False
        if len(name) > ManusSkillValidator.MAX_NAME_LENGTH:
            return False
        return True

    @staticmethod
    def validate_description(description: str) -> bool:
        """Validates if the description is within max length and contains no angle brackets."""
        if not isinstance(description, str):
            return False
        if len(description) > ManusSkillValidator.MAX_DESCRIPTION_LENGTH:
            return False
        if '<' in description or '>' in description:
            return False
        return True

    @staticmethod
    def validate_frontmatter_fields(frontmatter: dict) -> bool:
        """Validates if only allowed frontmatter fields are present."""
        if not isinstance(frontmatter, dict):
            return False
        return all(field in ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS for field in frontmatter.keys())

    @staticmethod
    def validate_manus_skill(skill_content: str) -> list[str]:
        """Validates a complete Manus SKILL.md content and returns a list of errors."""
        errors = []
        try:
            parts = skill_content.split('---\n', 2)
            if len(parts) < 3:
                errors.append("SKILL.md must have YAML frontmatter delimited by '---'.")
                return errors

            frontmatter_str = parts[1]
            frontmatter = yaml.safe_load(frontmatter_str)

            if not frontmatter:
                errors.append("Frontmatter is empty or invalid YAML.")
                return errors

            if 'name' not in frontmatter:
                errors.append("Frontmatter missing 'name' field.")
            elif not ManusSkillValidator.validate_name(frontmatter['name']):
                errors.append(f"Invalid name format: '{frontmatter['name']}'. Must be hyphen-case, lowercase, max {ManusSkillValidator.MAX_NAME_LENGTH} chars.")

            if 'description' not in frontmatter:
                errors.append("Frontmatter missing 'description' field.")
            elif not ManusSkillValidator.validate_description(frontmatter['description']):
                errors.append(f"Invalid description: '{frontmatter['description']}'. Max {ManusSkillValidator.MAX_DESCRIPTION_LENGTH} chars, no angle brackets.")

            if not ManusSkillValidator.validate_frontmatter_fields(frontmatter):
                unsupported_fields = set(frontmatter.keys()) - ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS
                errors.append(f"Unsupported frontmatter fields found: {', '.join(unsupported_fields)}. Allowed: {', '.join(ManusSkillValidator.ALLOWED_FRONTMATTER_FIELDS)}.")

        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error in frontmatter: {e}")
        except Exception as e:
            errors.append(f"An unexpected error occurred during validation: {e}")

        return errors

