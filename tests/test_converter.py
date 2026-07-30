import pytest
import inspect
import yaml
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
            ],
            "body_rules": [
                {
                    "id": "openclaw-workspace-path",
                    "pattern": r'~\/\.openclaw\/workspace\/',
                    "replacement": '/home/ubuntu/workspace/',
                    "log": "Replaced OpenClaw workspace path.",
                },
                {
                    "id": "openclaw-skills-path",
                    "pattern": r'~\/\.openclaw\/skills\/',
                    "replacement": '/home/ubuntu/skills/',
                    "log": "Replaced OpenClaw skills path.",
                },
                {
                    "id": "clawdhub-install",
                    "pattern": r'clawdhub install [a-zA-Z0-9-]+',
                    "replacement": 'Manus: To install skills, place them in `/home/ubuntu/skills/` directory.',
                    "log": "Replaced clawdhub install command.",
                },
                {
                    "id": "openclaw-hooks-enable",
                    "pattern": r'openclaw hooks enable',
                    "replacement": 'Manus: Hooks are not directly supported.',
                    "log": "Replaced openclaw hooks enable.",
                },
                {
                    "id": "claude-md-to-soul-md",
                    "pattern": r'(?<![A-Za-z0-9_.-])CLAUDE\.md(?![A-Za-z0-9_.])',
                    "replacement": 'soul.md',
                    "log": "Replaced CLAUDE.md with soul.md ({count} occurrence{plural}).",
                },
                {
                    "id": "agents-md-to-subtasks-md",
                    "pattern": r'(?<![A-Za-z0-9_.-])AGENTS\.md(?![A-Za-z0-9_.])',
                    "replacement": 'subtasks.md',
                    "log": "Replaced AGENTS.md with subtasks.md ({count} occurrence{plural}).",
                },
            ],
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


# --- New behavior: bracket rejection in description ---


@pytest.mark.parametrize(
    "angle_bracket",
    ["<", ">"],
)
def test_description_with_angle_brackets_is_rejected(converter, angle_bracket):
    """Descriptions containing angle brackets must NOT be silently stripped —
    the converter rejects them so the author can rewrite. The validator will
    then surface a clear frontmatter error rather than the user seeing a
    corrupted description."""
    clawhub_skill = inspect.cleandoc(f"""
        ---
        name: bracket-test
        description: "Use the {angle_bracket}shell{angle_bracket} tool."
        ---
        ## How To Use
        Step 1.
    """)
    manus_content, report = converter.convert(clawhub_skill)

    # Description should be cleared (becomes empty in the frontmatter)
    assert any(
        "Removed description for skill 'bracket-test'" in item for item in report
    ), f"Expected rejection message in report, got {report}"
    # The bracketed phrase must NOT survive in the output via silent stripping
    assert f"Use the {angle_bracket}shell{angle_bracket} tool." not in manus_content
    # The validator should then flag the (now empty) description.
    assert any(
        "Invalid description" in item and "no angle brackets" in item
        for item in report
    ), f"Expected validation error for empty description, got {report}"


# --- New behavior: filename replacements for AGENTS.md / CLAUDE.md ---


def test_agents_md_replaced_with_subtasks_md(converter):
    """AGENTS.md must become subtasks.md, not the long-form prose that
    previously broke filename references inside backticks."""
    clawhub_skill = inspect.cleandoc("""
        ---
        name: agents-md-test
        description: "Testing AGENTS.md replacement"
        ---
        ## How To Use
        - Promote learnings to `AGENTS.md`
        - See `AGENTS.md` for full reference
    """)
    manus_content, report = converter.convert(clawhub_skill)
    body = manus_content.split("---\n", 2)[2]

    # Replacement happened in the body
    assert "`subtasks.md`" in body
    assert "AGENTS.md" not in body
    # Replacement was logged
    assert any(
        "Replaced AGENTS.md with subtasks.md" in item for item in report
    )


def test_claude_md_replaced_with_soul_md(converter):
    """CLAUDE.md must become soul.md without the parenthesised explanation
    inserted inline."""
    clawhub_skill = inspect.cleandoc("""
        ---
        name: claude-md-test
        description: "Testing CLAUDE.md replacement"
        ---
        ## How To Use
        - Promote patterns to `CLAUDE.md`
        - See `CLAUDE.md` for examples
    """)
    manus_content, report = converter.convert(clawhub_skill)
    body = manus_content.split("---\n", 2)[2]

    assert "`soul.md`" in body
    assert "CLAUDE.md" not in body
    assert "Manus equivalent for core behavioral patterns" not in body
    assert any(
        "Replaced CLAUDE.md with soul.md" in item for item in report
    )


def test_agents_md_and_claude_md_combined(converter):
    """When both files are referenced in one skill, both get replaced."""
    clawhub_skill = inspect.cleandoc("""
        ---
        name: combined-test
        description: "Testing both replacements"
        ---
        ## How To Use
        Promote from `CLAUDE.md` into `AGENTS.md`.
    """)
    manus_content, report = converter.convert(clawhub_skill)
    body = manus_content.split("---\n", 2)[2]
    assert "`soul.md`" in body
    assert "`subtasks.md`" in body
    assert "CLAUDE.md" not in body
    assert "AGENTS.md" not in body


def test_partial_filename_not_replaced(converter):
    """A filename like AGENTS.bak.md or 'my-AGENTS.md' (not the exact
    full filename) must NOT be touched — we use a regex anchored on the
    extension."""
    clawhub_skill = inspect.cleandoc("""
        ---
        name: no-partial-match
        description: "Testing partial filename non-match"
        ---
        ## How To Use
        Reference `CLAUDE.md.bak` and `my-CLAUDE.md` and `AGENTS.mdx`.
    """)
    manus_content, report = converter.convert(clawhub_skill)

    # These should survive because they aren't the exact filenames
    assert "CLAUDE.md.bak" in manus_content
    assert "my-CLAUDE.md" in manus_content
    assert "AGENTS.mdx" in manus_content
    # No replacement messages should have been logged
    assert not any("Replaced CLAUDE.md" in item for item in report)
    assert not any("Replaced AGENTS.md" in item for item in report)


# --- New behavior: empty frontmatter values are dropped ---


@pytest.mark.parametrize(
    "field, empty_value",
    [
        ("metadata", ""),       # Explicit empty string
        ("metadata", None),     # YAML null / Python None
        ("metadata", {}),       # Empty mapping
        ("allowed-tools", []),  # Empty list
    ],
)
def test_empty_frontmatter_values_are_dropped(converter, field, empty_value):
    """Empty/None frontmatter values must not be emitted as `metadata: null`
    or `metadata: ''` in the output — they should be dropped silently.
    Reproduction of the earlier `examples/output/.../metadata: null` bug.

    Inspects the dict-level result of `_transform_frontmatter` so it works
    independently of any yaml dump mocks in the test environment.
    """
    frontmatter = {
        "name": "empty-test",
        "description": "A valid description.",
        field: empty_value,
    }
    out = converter._transform_frontmatter(frontmatter)
    # The empty key must have been dropped.
    assert field not in out
    # Required keys still present.
    assert out["name"] == "empty-test"
    assert "description" in out


def test_nonempty_frontmatter_values_are_preserved(converter):
    """Sanity check: real values must survive the new empty-drop filter.

    Inspects the dict-level result of `_transform_frontmatter` so we are not
    dependent on yaml.dump/dump-mock output details (which can vary between
    real yaml and the conftest's mock).
    """
    frontmatter = {
        "name": "preserve-test",
        "description": "Valid description.",
        "license": "MIT",
        "metadata": {"author": "someone"},
    }
    out = converter._transform_frontmatter(frontmatter)
    assert out["license"] == "MIT"
    assert out["metadata"] == {"author": "someone"}
    # description enhancement should have added 'what it does'
    assert "what it does" in out["description"].lower()


# --- Plugin-style rules ---


def test_add_rule_runtime(converter):
    """Rules added at runtime via add_rule() should run alongside the
    config-loaded rules."""
    converter.add_rule({
        "id": "custom-greeting",
        "pattern": r"Hello",
        "replacement": "Hi",
        "log": "Replaced Hello with Hi ({count} occurrence{plural}).",
    })
    clawhub_skill = inspect.cleandoc("""
        ---
        name: custom-rule-test
        description: "Testing runtime-added rule."
        ---
        ## How To Use
        Hello and Hello again.
    """)
    _, report = converter.convert(clawhub_skill)
    body = converter._transform_body("Hello and Hello again.")
    assert body == "Hi and Hi again."
    # The plugin rule's log was emitted, and the count is accurate.
    assert any("Replaced Hello with Hi (2 occurrences)" in item for item in report)


def test_add_rule_validates_regex(converter):
    """An invalid regex should raise ValueError, not silently fail."""
    import pytest
    with pytest.raises(ValueError, match="Invalid pattern"):
        converter.add_rule({
            "id": "bad-regex",
            "pattern": r"[unclosed",
            "replacement": "x",
        })


def test_add_rule_accepts_unicode_and_multiline(converter):
    """Rules with multiline patterns and unicode in the replacement should
    work end-to-end."""
    converter.add_rule({
        "id": "unicode-rule",
        "pattern": r"§OLD§",
        "replacement": "§NEW§ — αβγ",
        "log": "Replaced §OLD§ with §NEW§.",
    })
    body = converter._transform_body("§OLD§ and §OLD§ again.")
    assert body == "§NEW§ — αβγ and §NEW§ — αβγ again."


def test_apply_body_rules_skips_malformed():
    """Body rules missing pattern or replacement are skipped with a warning,
    not silently raised."""
    from claw2manus.converter import _apply_body_rules
    rules = [
        {"id": "no-pattern", "replacement": "x"},
        {"id": "no-replacement", "pattern": "y"},
        {"id": "good", "pattern": "z", "replacement": "Z", "log": "Replaced z with Z ({count})."},
    ]
    body = "y and z"
    report = []
    out = _apply_body_rules(body, rules, report)
    # The good rule ran
    assert out == "y and Z"
    assert any("Replaced z with Z" in item for item in report)


def test_apply_body_rules_handles_invalid_regex():
    """An invalid regex in a rule is logged and skipped rather than raised."""
    from claw2manus.converter import _apply_body_rules
    rules = [
        {"id": "broken", "pattern": r"[unclosed", "replacement": "x"},
        {"id": "good", "pattern": r"a", "replacement": "A", "log": "ok"},
    ]
    body = "a a a"
    report = []
    out = _apply_body_rules(body, rules, report)
    # The broken rule didn't run, but the body was still passed through.
    # The good rule still applied.
    assert out == "A A A"


def test_compile_body_rules_drops_invalid():
    """The converter drops rules with invalid regex at construction time
    rather than failing the whole converter."""
    from claw2manus.converter import SkillConverter

    class _FakeLoad:
        def __call__(self, _path):
            return {
                "body_rules": [
                    {"id": "bad", "pattern": r"[unclosed", "replacement": "x"},
                    {"id": "good", "pattern": r"foo", "replacement": "bar",
                     "log": "Replaced foo with bar."},
                ],
                "tool_replacements": {},
                "stdio_patterns": [],
            }

    with patch.object(SkillConverter, "_load_config", _FakeLoad()):
        c = SkillConverter()
        # Only the valid rule survives
        assert len(c._body_rules) == 1
        assert c._body_rules[0]["id"] == "good"
