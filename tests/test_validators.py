import pytest
import inspect
from unittest.mock import patch
from claw2manus.validators import ManusSkillValidator
import yaml

def test_validate_name():
    assert ManusSkillValidator.validate_name("valid-name") == True
    assert ManusSkillValidator.validate_name("Invalid Name") == False
    assert ManusSkillValidator.validate_name("a" * 65) == False

def test_validate_description():
    assert ManusSkillValidator.validate_description("A valid description.") == True
    assert ManusSkillValidator.validate_description("No <brackets> allowed.") == False

@patch('yaml.safe_load')
def test_validate_manus_skill(mock_safe_load):
    mock_safe_load.return_value = {"name": "valid-skill", "description": "What it does: test. When to use it: test."}
    valid_skill = inspect.cleandoc("""
        ---
        name: valid-skill
        description: "What it does: test. When to use it: test."
        ---
        ## How To Use
        Step 1.
    """)
    errors = ManusSkillValidator.validate_manus_skill(valid_skill)
    assert len(errors) == 0

    mock_safe_load.return_value = {"name": "Invalid Name", "description": "<bracket>"}
    invalid_skill = inspect.cleandoc("""
        ---
        name: Invalid Name
        description: <bracket>
        ---
        Missing required section here.
    """)
    errors = ManusSkillValidator.validate_manus_skill(invalid_skill)
    assert len(errors) > 0
    assert any("Invalid name format" in e for e in errors)
    assert any("no angle brackets" in e for e in errors)
    assert any("Body missing a usage-related section" in e for e in errors)

@patch('yaml.safe_load')
def test_validate_manus_skill_yaml_error(mock_safe_load):
    mock_safe_load.side_effect = yaml.YAMLError("mock error")
    invalid_yaml_skill = inspect.cleandoc("""
        ---
        unclosed_string: "this
        ---
        ## How To Use
        Step 1.
    """)
    errors = ManusSkillValidator.validate_manus_skill(invalid_yaml_skill)
    assert len(errors) > 0
    assert any("YAML parsing error in frontmatter:" in e for e in errors)
