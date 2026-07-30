---
layout: default
title: Home
permalink: /
nav_order: 1
---

# claw2manus

**Convert [ClawHub](https://clawhub.ai) skills into [Manus](https://manus.im)-compatible skills.**

A small, fast, fully-tested Python CLI that translates OpenClaw `SKILL.md`
files to Manus format in one pass — frontmatter cleanup, body rewriting,
GitHub fetching, and a change report you can actually audit.

## Start here

- **[Installation](../README.md#install)** — get the CLI on your machine.
- **[Quickstart](../README.md#quickstart)** — convert your first skill in five minutes.

## Documentation guide

### For users

- **[Conversion Logic](CONVERSION.md)** — what each stage of the converter actually does.
- **[Configuration Guide](CONFIGURATION.md)** — `config.yaml` schema and how to add body rules.
- **[Development Guide](DEVELOPMENT.md)** — project layout, test setup, contributing.

### For reference

- **[README](../README.md)** — full project readme with feature matrix, commands, exit codes, and project layout.
- **[Changelog](../CHANGELOG.md)** — version history and audit fixes.

### Command reference

| Command | Use it for |
| --- | --- |
| `claw2manus convert <path>` | Convert a single SKILL.md file. |
| `claw2manus convert-all <dir>` | Convert every SKILL.md in a directory tree. |
| `claw2manus fetch-and-convert <name\|url>` | Pull from ClawHub / GitHub and convert. |
| `claw2manus validate <path>` | Check an existing SKILL.md against Manus rules. |

## Why use it

- **One command, one directory.** `convert-all` walks a tree of skills,
  emits clean Manus output, and never collides on names — even when two
  skills share an author.
- **Auditable.** Every body substitution is a configurable rule in
  `config.yaml`. Add yours without touching code.
- **Honest about what it can't do.** No silent `CLAUDE.md` →
  three-paragraph prose rewrites — your references stay as filenames.
  No silent bracket stripping that masks bugs — descriptions with `<` or
  `>` are rejected so the validator can flag them.
- **Respects auth.** Set `GITHUB_TOKEN` and you'll get the 5,000 req/hr
  GitHub limit instead of 60. Anonymous use still works.

## Project status

| | |
| --- | --- |
| Version | 0.1.0 |
| Python | 3.10 · 3.11 · 3.12 |
| Tests | 92 passing |
| CI | GitHub Actions on every push and tag |
| Docs theme | [`jekyll-theme-console`](https://github.com/b2a3e8/jekyll-theme-console) |
| Repository | [github.com/frostmute/claw2manus](https://github.com/frostmute/claw2manus) |
