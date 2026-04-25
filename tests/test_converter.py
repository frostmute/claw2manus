import pytest
import inspect
from unittest.mock import patch, MagicMock
from claw2manus.converter import SkillConverter

@pytest.fixture
def converter():
    # Use patch.object to mock _load_config for all tests using this fixture
    # This avoids dependency on a physical config.yaml and keep tests deterministic
    with patch.object(SkillConverter, '_load_config') as mock_load:
        mock_load.return_value = {
            "tool_replacements": {
                "sessions_list": "Manus: Use `shell` tool with `ps aux` or similar to list processes, or `gws` to list Google Workspace sessions."
            },
            "stdio_patterns": [
                {
                    "pattern": r'(\b(?:python|node|ruby|perl|php|java|go|bash|sh|zsh)\b\s+.*?\.py)',
                    "category": "Script execution",
                    "mcp_suggestion": "Check if this can be handled via standard `shell` or if a dedicated MCP bridge is needed."
                },
                {
                    "pattern": r'(\b(?:cat|less|more|tail|head|grep|awk|sed)\b)',
                    "category": "Text processing utilities",
                    "mcp_suggestion": "Standard `shell` tools are usually sufficient."
                }
            ]
        }
        yield SkillConverter()

def test_basic_conversion(converter):
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

def test_stdio_detection(converter):
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

def test_missing_description(converter):
    clawhub_skill = inspect.cleandoc("""
        ---
        name: No Description
        ---
        # Body
    """)
    manus_content, report = converter.convert(clawhub_skill)
    assert "description: 'What it does: A skill derived from ClawHub." in manus_content

def test_validation_error_in_report(converter):
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

def test_malformed_yaml_frontmatter(converter):
    import yaml

    clawhub_skill = inspect.cleandoc("""
        ---
        name: Test Skill
        description: "Malformed YAML (missing closing quote)
        ---
        # Body
    """)

    # We use a malformed string but still need to mock safe_load to raise YAMLError
    # because our mock_safe_load is too simple to catch all YAML errors.
    with patch("yaml.safe_load") as mock_safe_load:
        mock_safe_load.side_effect = yaml.YAMLError("Scanner error: expected <block end>")

        manus_content, report = converter.convert(clawhub_skill)

        # In case of YAML error, it should return the original content and log the error
        assert manus_content == clawhub_skill
        assert any("YAML parsing error in frontmatter:" in item for item in report)
        assert any("Scanner error: expected <block end>" in item for item in report)
