import os
import tempfile

import pytest
from unittest.mock import patch
from claw2manus.cli import (
    _safe_dir_name,
    _skill_name_from_path,
    on_unresolved_tool_cli,
)


@pytest.mark.parametrize(
    "user_input, expected_result",
    [
        ("Use my custom tool", "Use my custom tool"),
        ("", "Use default tool"),
        ("   Use my custom tool   ", "Use my custom tool"),
        ("   ", "Use default tool"),
    ],
)
def test_on_unresolved_tool_cli(user_input, expected_result, capsys):
    with patch(
        "builtins.input", return_value=user_input
    ) as mocked_input:
        result = on_unresolved_tool_cli("unknown_tool", "Use default tool")
        assert result == expected_result

        mocked_input.assert_called_once_with(
            "Enter custom instruction (or press Enter to use default): "
        )
        captured = capsys.readouterr()
        assert "Unresolved tool mapping found: 'unknown_tool'" in captured.out
        assert "Default instruction: Use default tool" in captured.out


# --- _safe_dir_name ---


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("normal-name", "normal-name"),
        ("foo_bar", "foo_bar"),
        ("foo.bar", "foo.bar"),
        ("foo/bar", "foo-bar"),
        ("foo\\bar", "foo-bar"),
        ("foo/bar/baz", "foo-bar-baz"),
        ("..", "converted-skill"),
        ("../etc", "etc"),
        ("../../etc/passwd", "etc-passwd"),
        ("   ", "converted-skill"),
        ("", "converted-skill"),
        ("  ../trailing  ", "trailing"),
        # characters outside the safe alphabet are NOT silently dropped —
        # the function rejects to a safe default.
        ("foo;rm -rf", "converted-skill"),
        ("foo$bar", "converted-skill"),
        (".", "converted-skill"),
    ],
)
def test_safe_dir_name(raw, expected):
    assert _safe_dir_name(raw) == expected


def test_safe_dir_name_never_returns_traversal():
    """Whatever garbage goes in, the output must not traverse out of a parent dir."""
    for raw in [
        "../", "../../../",
        "..", "../..", "/etc/passwd",
        "  /absolute\\path  ",
        "subdir/../../../escape",
        "name\x00null",
    ]:
        out = _safe_dir_name(raw)
        assert ".." not in out.split(os.sep)
        assert not out.startswith("/")
        assert not out.startswith("\\")
        assert "\x00" not in out


# --- _print_diff ---


def test_print_diff_shows_changes(capsys):
    """The diff helper should print unified-diff output for changed inputs."""
    from claw2manus.cli import _print_diff
    before = "line one\nline two\n"
    after = "line one\nLINE TWO\nline three\n"
    _print_diff("SKILL.md", before, after)
    out = capsys.readouterr().out
    # The header lines and the changed lines should appear
    assert "a/SKILL.md" in out
    assert "b/SKILL.md" in out
    assert "-line two" in out
    assert "+LINE TWO" in out
    assert "+line three" in out


def test_print_diff_no_changes(capsys):
    """When input and output are identical (excluding line endings), it says so."""
    from claw2manus.cli import _print_diff
    text = "alpha\nbeta\n"
    _print_diff("SKILL.md", text, text)
    out = capsys.readouterr().out
    assert "No textual changes" in out


def test_print_diff_handles_path_with_slashes(capsys):
    """Diff labels should use the basename of the input path."""
    from claw2manus.cli import _print_diff
    _print_diff("/some/long/path/SKILL.md", "a\n", "b\n")
    out = capsys.readouterr().out
    assert "a/SKILL.md" in out
    assert "b/SKILL.md" in out


# --- convert_skill with --diff ---


def test_convert_skill_diff_mode_emits_diff(capsys, tmp_path):
    """`convert_skill(..., show_diff=True)` prints a unified diff in addition to
    the report and (since dry_run is True in this test) the output."""
    from claw2manus.cli import convert_skill

    input_path = tmp_path / "input.md"
    input_path.write_text(
        "---\nname: Test Skill\ndescription: \"A test skill.\"\n"
        "---\n\n# Body\n# Old heading\n"
    )

    convert_skill(
        input_path=str(input_path),
        output_dir=str(tmp_path / "out"),
        dry_run=True,
        interactive=False,
        show_diff=True,
    )

    captured = capsys.readouterr().out
    # Diff section was printed
    assert "Unified Diff" in captured
    assert "# Old heading" in captured


# --- _skill_name_from_path ---


def test_skill_name_single_segment():
    """A flat structure should keep the parent directory name."""
    assert _skill_name_from_path(
        "/tmp/skills/foo/SKILL.md", "/tmp/skills"
    ) == "foo"


def test_skill_name_nested_disambiguation():
    """Nested skills under the same author must NOT collide."""
    a = _skill_name_from_path("/tmp/skills/author/skillA/SKILL.md", "/tmp/skills")
    b = _skill_name_from_path("/tmp/skills/author/skillB/SKILL.md", "/tmp/skills")
    assert a == "author-skillA"
    assert b == "author-skillB"
    assert a != b


def test_skill_name_falls_back_when_no_relative_path():
    """If input_dir is not a prefix of the skill path, use immediate parent."""
    # /etc and /tmp don't share; falls back to the parent dir name
    assert _skill_name_from_path(
        "/tmp/foo/SKILL.md", "/etc"
    ) == "foo"


def test_skill_name_handles_real_examples_layout():
    """Match the actual examples/ layout used in the project."""
    project = "/root/repos/claw2manus"
    name = _skill_name_from_path(
        f"{project}/examples/input/self-improving-agent/SKILL.md",
        f"{project}/examples/input",
    )
    assert name == "self-improving-agent"


def test_skill_name_filename_only():
    """When the input_dir is the directory containing SKILL.md, use the file name."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "lonely-skill.md")
        name = _skill_name_from_path(path, d)
        # last component is a file, so the function uses its base name
        assert name == "lonely-skill"
