import pytest
import inspect
from claw2manus.converter import SkillConverter

def test_basic_conversion():
    converter = SkillConverter()
    clawhub_skill = inspect.cleandoc("""
        ---
        name: Test Skill
        description: "A test skill."
        ---
        # Body
        ~/.openclaw/workspace/test
        sessions_list
    """)
    manus_content, report = converter.convert(clawhub_skill)
    
    assert "name: test-skill" in manus_content
    assert "What it does: A test skill." in manus_content
    assert "/home/ubuntu/workspace/test" in manus_content
    assert "Manus: Use `shell` tool" in manus_content
    assert any("Replaced OpenClaw tool 'sessions_list'" in item for item in report)

def test_stdio_detection():
    converter = SkillConverter()
    clawhub_skill = inspect.cleandoc("""
        ---
        name: Stdio Test
        description: "Testing stdio detection."
        ---
        # Body
        python script.py
        grep "pattern" file.txt
    """)
    manus_content, report = converter.convert(clawhub_skill)
    
    assert any("Potential stdio-only tool detected (Script execution)" in item for item in report)
    assert any("Potential stdio-only tool detected (Text processing utilities)" in item for item in report)

def test_missing_description():
    converter = SkillConverter()
    clawhub_skill = inspect.cleandoc("""
        ---
        name: No Description
        ---
        # Body
    """)
    manus_content, report = converter.convert(clawhub_skill)
    assert "description: 'What it does: A skill derived from ClawHub." in manus_content

def test_validation_error_in_report():
    converter = SkillConverter()
    # Name too long
    clawhub_skill = inspect.cleandoc("""
        ---
        name: a-very-long-name-that-exceeds-sixty-four-characters-and-should-trigger-a-validation-error-if-not-truncated
        description: "Testing validation."
        ---
        # Body
        ## How To Use
        Step 1.
    """)
    manus_content, report = converter.convert(clawhub_skill)
    assert any("Truncated skill name" in item for item in report)
