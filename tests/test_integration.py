"""End-to-end integration tests against a small synthetic repo.

These tests run the conversion pipeline against a real on-disk repository
fixture, without mocking yaml/requests/etc. They are not network-gated by
default — the fixture is local — but they are slow (full converter cycle
per skill) so a marker could be added if test time becomes a concern.

If real `yaml`, `requests`, or `bs4` aren't available, these tests skip.
"""
import os
import shutil

import pytest

from claw2manus.converter import SkillConverter
from claw2manus.cli import convert_all_skills


def _package_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


yaml_available = _package_available("yaml")
pytestmark = pytest.mark.skipif(
    not yaml_available, reason="PyYAML not installed; integration test requires real yaml"
)


FIXTURE_ROOT = os.path.join(os.path.dirname(__file__), "fixtures", "integration_repo")


@pytest.fixture
def fixture_repo(tmp_path):
    """Copy the synthetic repo into a tmp dir and yield its path.

    Tests get an isolated copy so they don't pollute the committed fixture.
    """
    if not os.path.isdir(FIXTURE_ROOT):
        pytest.skip(f"Integration repo fixture missing at {FIXTURE_ROOT}")
    dest = tmp_path / "input"
    shutil.copytree(FIXTURE_ROOT, dest)
    return dest


def test_fixture_repo_layout(fixture_repo):
    """Sanity: the fixture has the expected shape."""
    sk_paths = []
    for root, _, files in os.walk(fixture_repo):
        for f in files:
            if f == "SKILL.md":
                sk_paths.append(os.path.join(root, f))
    assert len(sk_paths) == 3, f"Expected 3 SKILL.md files, got {len(sk_paths)}"
    parents = {os.path.basename(os.path.dirname(p)) for p in sk_paths}
    assert parents == {"skill-alpha", "skill-beta", "another-one"}


def test_full_convert_all_skills(fixture_repo, tmp_path):
    """Run the full converter on the integration fixture and check the output
    is structurally correct and contains the expected substitutions."""
    output_dir = tmp_path / "output"
    convert_all_skills(
        input_dir=str(fixture_repo),
        output_dir=str(output_dir),
        interactive=False,
    )

    # The three skill files should all exist
    sk_files = []
    for root, _, files in os.walk(output_dir):
        for f in files:
            if f == "SKILL.md":
                sk_files.append(os.path.join(root, f))
    assert len(sk_files) == 3, f"Expected 3 output SKILL.md files, got {len(sk_files)}"

    # Each output should have:
    #  - a CONVERSION_REPORT.md sibling
    #  - no `~/.openclaw/` paths in the body
    #  - substitutions applied in the frontmatter (no angle brackets etc.)
    for sk in sk_files:
        out_dir = os.path.dirname(sk)
        body = open(sk).read()
        # CONVERSION_REPORT.md sibling
        assert os.path.exists(os.path.join(out_dir, "CONVERSION_REPORT.md")), out_dir

    # Look for the body transformations specifically
    all_bodies = "\n\n".join(open(s).read() for s in sk_files)
    # OpenClaw paths replaced (alpha had one)
    assert "~/.openclaw/" not in all_bodies
    # The 'sessions_list' tool (in alpha) should be replaced with the Manus instruction
    assert "sessions_list" not in all_bodies, "Unresolved tool replacement"
    assert "Manus: Use `shell` tool with `ps aux`" in all_bodies
    # AGENTS.md reference should be replaced
    assert "AGENTS.md" not in all_bodies or "subtasks.md" in all_bodies
    # CLAUDE.md reference should be replaced
    assert "CLAUDE.md" not in all_bodies or "soul.md" in all_bodies


def test_skills_under_same_author_disambiguate(fixture_repo, tmp_path):
    """Two skills under author-a (skill-alpha and another-one) must produce
    different output directory names — the audit case where they could have
    collided."""
    output_dir = tmp_path / "output"
    convert_all_skills(
        input_dir=str(fixture_repo),
        output_dir=str(output_dir),
        interactive=False,
    )

    out_subdirs = sorted(os.listdir(output_dir))
    # Expect author-a-skill-alpha, author-b-skill-beta, author-a-another-one
    # (3 distinct names; not 2 — the shared-author case is the one being tested).
    assert len(out_subdirs) == 3, (
        f"Expected 3 distinct output directories, got {out_subdirs}"
    )
    # None of the names should contain '..' (no traversal)
    for name in out_subdirs:
        assert ".." not in name, f"Output name contains traversal: {name}"


def test_conversion_report_records_substitutions(fixture_repo, tmp_path):
    """The CONVERSION_REPORT.md files should accurately reflect what changed."""
    output_dir = tmp_path / "output"
    convert_all_skills(
        input_dir=str(fixture_repo),
        output_dir=str(output_dir),
        interactive=False,
    )
    # Find the alpha-skill output (it had the most substitutions)
    candidates = []
    for root, _, files in os.walk(output_dir):
        if "skill-alpha" in root and "CONVERSION_REPORT.md" in files:
            candidates.append(os.path.join(root, "CONVERSION_REPORT.md"))
    assert len(candidates) == 1, candidates
    report = open(candidates[0]).read()
    # The bodies are: CLAUDE.md replacement, AGENTS.md replacement, openclaw path,
    # session_list replacement
    assert "Replaced OpenClaw" in report
    assert "Replaced CLAUDE.md" in report
    assert "Replaced OpenClaw tool 'sessions_list'" in report


def test_individual_skill_convert_via_skill_converter(fixture_repo):
    """Convert a single fixture skill through SkillConverter directly."""
    c = SkillConverter()
    src_path = os.path.join(fixture_repo, "author-a", "skill-alpha", "SKILL.md")
    with open(src_path) as f:
        converted, report = c.convert(f.read())

    # The conversion succeeded (no early-return on YAML error)
    assert "---" in converted
    # The tool was replaced in the body
    assert "sessions_list" not in converted.split("---", 2)[2]
    # The OpenClaw path was replaced
    assert "~/.openclaw/" not in converted
    # The report captured the changes
    joined = "\n".join(report)
    assert "Replaced OpenClaw" in joined
