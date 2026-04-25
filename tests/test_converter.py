import pytest
import inspect
from unittest.mock import patch, MagicMock
from claw2manus.converter import SkillConverter
import yaml

@patch('yaml.safe_load')
def test_basic_conversion(mock_safe_load):
    # Mock config
    mock_safe_load.return_value = {
        "tool_replacements": {
            "~/.openclaw/workspace": "/home/ubuntu/workspace",
            "sessions_list": "Manus: Use `shell` tool",
            "python": "Manus: Use `python` tool"
        },
        "stdio_patterns": [
            {"pattern": "python ", "category": "Script execution"},
            {"pattern": "grep ", "category": "Text processing utilities"}
        ]
    }
    converter = SkillConverter()

    # Mock frontmatter for skill parsing
    mock_safe_load.return_value = {
        "name": "Test Skill",
        "description": "A test skill."
    }

    clawhub_skill = inspect.cleandoc("""
        ---
        name: Test Skill
        description: "A test skill."
        ---
        # Body
        ~/.openclaw/workspace/test
        sessions_list
    """)
    
    # Needs a mock for yaml.dump
    with patch('yaml.dump', return_value="---\nname: test-skill\ndescription: 'What it does: A test skill.. When to use it: This is a converted skill from ClawHub, review its content for usage instructions.'\n---\n"):
        manus_content, report = converter.convert(clawhub_skill)

        assert "name: test-skill" in manus_content
        assert "What it does: A test skill." in manus_content
        assert "/home/ubuntu/workspace/test" in manus_content
        assert "Manus: Use `shell` tool" in manus_content
        assert any("Replaced OpenClaw tool 'sessions_list'" in item for item in report)

@patch('yaml.safe_load')
def test_stdio_detection(mock_safe_load):
    # Need to simulate the config loading first, then the frontmatter parsing
    mock_safe_load.side_effect = [
        {
            "tool_replacements": {},
            "stdio_patterns": [
                {"pattern": "python script.py", "category": "Script execution"},
                {"pattern": "grep \"pattern\"", "category": "Text processing utilities"}
            ]
        },
        {
            "name": "Stdio Test",
            "description": "Testing stdio detection."
        }
    ]
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
    with patch('yaml.dump', return_value="---\nname: stdio-test\ndescription: 'What it does: Testing stdio detection.. When to use it: This is a converted skill from ClawHub, review its content for usage instructions.'\n---\n"):
        manus_content, report = converter.convert(clawhub_skill)

        assert any("Potential stdio-only tool detected (Script execution)" in item for item in report)
        assert any("Potential stdio-only tool detected (Text processing utilities)" in item for item in report)

@patch('yaml.safe_load')
def test_missing_description(mock_safe_load):
    mock_safe_load.side_effect = [
        {}, # config
        {"name": "No Description"} # frontmatter
    ]
    converter = SkillConverter()
    clawhub_skill = inspect.cleandoc("""
        ---
        name: No Description
        ---
        # Body
    """)
    with patch('yaml.dump', return_value="---\nname: no-description\ndescription: 'What it does: A skill derived from ClawHub. When to use it: This is a converted skill from ClawHub, review its content for usage instructions.'\n---\n"):
        manus_content, report = converter.convert(clawhub_skill)
        assert "description: 'What it does: A skill derived from ClawHub." in manus_content

@patch('yaml.safe_load')
def test_validation_error_in_report(mock_safe_load):
    mock_safe_load.side_effect = [
        {}, # config
        {
            "name": "a-very-long-name-that-exceeds-sixty-four-characters-and-should-trigger-a-validation-error-if-not-truncated",
            "description": "Testing validation."
        }
    ]
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
    with patch('yaml.dump', return_value="---\nname: a-very-long-name-that-exceeds-sixty-four-characters-and-shou\ndescription: 'What it does: Testing validation.. When to use it: This is a converted skill from ClawHub, review its content for usage instructions.'\n---\n"):
        manus_content, report = converter.convert(clawhub_skill)
        assert any("Truncated skill name" in item for item in report)
