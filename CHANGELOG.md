# Changelog

All notable changes to `claw2manus` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `convert --diff` flag for unified-diff review of a single conversion.
- Plugin-style `body_rules` in `config.yaml` so users can add their own
  body substitutions without editing source.
- `SkillConverter.add_rule(...)` API for programmatic rule registration
  with up-front regex validation.
- Optional `GITHUB_TOKEN` support that lifts GitHub's request limit from
  60 to 5,000 req/hr when set.
- End-to-end integration tests in `tests/test_integration.py` against a
  synthetic three-skill fixture repo.
- GitHub Actions workflow running `pytest` on Python 3.10, 3.11, 3.12.
- `pre-commit` configuration with `ruff` and hygiene hooks.
- `pyproject.toml` with project metadata and tool configuration.

### Changed
- `CLAUDE.md` and `AGENTS.md` references are now replaced with the literal
  filenames `soul.md` and `subtasks.md` (not long-form prose) using
  word-bounded regexes.
- Descriptions containing `<` or `>` are now *rejected* instead of silently
  stripped, so validators can flag empty descriptions clearly.
- Empty / null frontmatter values (`""`, `None`, `[]`, `{}`) are dropped
  before `yaml.dump` so output never contains `metadata: null` noise.
- `_safe_dir_name()` and `_skill_name_from_path()` helpers sanitize output
  directory names to prevent `..` traversal and to disambiguate skills
  under a shared author.
- `setup.py` removed in favor of declarative `pyproject.toml`.

### Fixed
- The committed example output (`examples/output/.../SKILL.md`) showed
  malformed filename replacement and now matches the converter's actual
  output.
- The duplicated `~/.openclaw/` path-replacement now has an explicit
  `id` and `log` template that reports accurate occurrence counts.
- The "Replaced CLAUDE.md" report entry no longer fires when zero matches
  were made.

## [0.1.0] — Initial release

- Batch conversion (`convert-all`)
- Skill fetching from ClawHub / GitHub (`fetch-and-convert`)
- Interactive tool-replacement overrides (`--interactive`)
- Manus skill validation (`validate`)
- Conversion-report generation (`CONVERSION_REPORT.md`)
- Bundled `config.yaml` with tool replacements and stdio patterns

[Unreleased]: https://github.com/frostmute/claw2manus/compare/main...HEAD
[0.1.0]: https://github.com/frostmute/claw2manus/releases/tag/v0.1.0
