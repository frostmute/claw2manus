import pytest
import inspect
from claw2manus.validators import ManusSkillValidator

def test_validate_name():
    assert ManusSkillValidator.validate_name("valid-name") == True
    assert ManusSkillValidator.validate_name("Invalid Name") == False
    assert ManusSkillValidator.validate_name("a" * 65) == False

def test_validate_description():
    assert ManusSkillValidator.validate_description("A valid description.") == True
    assert ManusSkillValidator.validate_description("No <brackets> allowed.") == False

def test_validate_manus_skill():
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
