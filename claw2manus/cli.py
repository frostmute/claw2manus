import argparse
import difflib
import os
import shutil
import glob
import re
import logging
from claw2manus.converter import SkillConverter
from claw2manus.fetcher import SkillFetcher
from claw2manus.validators import ManusSkillValidator

def on_unresolved_tool_cli(tool_name, default_instruction):
    print(f"\nUnresolved tool mapping found: '{tool_name}'")
    print(f"Default instruction: {default_instruction}")
    user_input = input("Enter custom instruction (or press Enter to use default): ").strip()
    return user_input if user_input else default_instruction

def _print_conversion_report(report: list[str]) -> None:
    print("\n--- Conversion Report ---")
    if report:
        for item in report:
            print(f"- {item}")
    else:
        print("No specific changes noted during conversion.")
    print("-------------------------")


def _print_diff(input_path: str, input_text: str, output_text: str) -> None:
    """Print a unified diff between the input SKILL.md and the converted output.

    Useful when reviewing what the converter actually changed — `--dry-run`
    shows the full output, but a diff highlights exactly which lines moved.
    """
    from_name = os.path.basename(input_path) if input_path else "input.md"
    diff = difflib.unified_diff(
        input_text.splitlines(keepends=True),
        output_text.splitlines(keepends=True),
        fromfile=f"a/{from_name}",
        tofile=f"b/{from_name}",
        lineterm="",
    )
    lines = list(diff)
    if not lines:
        print("\nNo textual changes (only frontmatter/reporting).")
        return
    print("\n--- Unified Diff (input -> output) ---")
    for line in lines:
        print(line)
    print("--------------------------------------")

def save_conversion_results(output_dir, skill_name, content, report, original_path=None):
    os.makedirs(output_dir, exist_ok=True)
    
    # Save SKILL.md
    skill_path = os.path.join(output_dir, "SKILL.md")
    with open(skill_path, "w") as f:
        f.write(content)
    
    # Save CONVERSION_REPORT.md
    report_path = os.path.join(output_dir, "CONVERSION_REPORT.md")
    with open(report_path, "w") as f:
        f.write(f"# Conversion Report for {skill_name}\n\n")
        if report:
            for item in report:
                f.write(f"- {item}\n")
        else:
            f.write("No specific changes noted during conversion.\n")

    # Automatic soul.md generation
    if original_path:
        original_dir = os.path.dirname(original_path)
        claude_md_path = os.path.join(original_dir, "CLAUDE.md")
        if os.path.exists(claude_md_path):
            soul_md_path = os.path.join(output_dir, "soul.md")
            shutil.copy(claude_md_path, soul_md_path)
            print(f"Automatically generated soul.md from CLAUDE.md")

    return skill_path

def convert_skill(input_path: str, output_dir: str, dry_run: bool, interactive: bool = False, show_diff: bool = False):
    converter = SkillConverter()


    with open(input_path, "r") as f:
        clawhub_skill_content = f.read()

    manus_skill_content, report = converter.convert(
        clawhub_skill_content,
        interactive=interactive,
        on_unresolved_tool=on_unresolved_tool_cli if interactive else None
    )

    _print_conversion_report(report)

    if show_diff:
        _print_diff(input_path, clawhub_skill_content, manus_skill_content)

    if not dry_run:
        # derive skill name from directory or file name
        skill_name = os.path.basename(os.path.dirname(input_path)) or "converted-skill"
        if not os.path.dirname(input_path):
             skill_name = input_path.replace(".md", "")
        skill_name = _safe_dir_name(skill_name)

        output_skill_dir = os.path.join(output_dir, skill_name)
        save_conversion_results(output_skill_dir, skill_name, manus_skill_content, report, input_path)
        print(f"\nConverted skill saved to: {output_skill_dir}")
    else:
        print("\n--- Converted Skill (Dry Run) ---")
        print(manus_skill_content)
        print("---------------------------------")

def _safe_dir_name(name: str) -> str:
    """Sanitize a string for use as an output directory name.

    Strips path separators and traversal sequences so a malformed skill_name
    (e.g. derived from a fetched URL) cannot escape the output directory.
    Returns 'converted-skill' when nothing usable remains.
    """
    # Replace path separators and traversal characters with '-'
    cleaned = re.sub(r"[\\/]+", "-", name)
    cleaned = cleaned.replace("..", "-")
    cleaned = cleaned.strip().strip(".-")
    if not cleaned or not re.match(r"^[A-Za-z0-9._-]+$", cleaned):
        return "converted-skill"
    return cleaned


def _skill_name_from_path(skill_file: str, input_dir: str) -> str:
    """Derive a stable, collision-resistant skill name from a SKILL.md path.

    Uses the path relative to input_dir so multiple skills under a single
    parent directory (e.g. input/author/{a,b}/SKILL.md) don't overwrite each
    other. Falls back to the immediate parent directory name if input_dir
    isn't a prefix of skill_file.
    """
    abs_input = os.path.abspath(input_dir)
    abs_skill = os.path.abspath(skill_file)
    try:
        rel = os.path.relpath(abs_skill, abs_input)
    except ValueError:
        return os.path.basename(os.path.dirname(abs_skill)) or "converted-skill"
    # If input_dir isn't a prefix of skill_file, relpath starts with '..'.
    # Fall back to the immediate parent directory's name so we don't emit
    # traversal sequences as part of a derived name.
    if rel.split(os.sep)[0] == "..":
        return os.path.basename(os.path.dirname(abs_skill)) or "converted-skill"
    parts = rel.split(os.sep)
    # drop the trailing SKILL.md
    parts = parts[:-1]
    if not parts:
        return os.path.basename(skill_file).replace(".md", "") or "converted-skill"
    # Use the full relative path joined with '-' to preserve disambiguation
    return "-".join(parts) if len(parts) > 1 else parts[0]


def convert_all_skills(input_dir: str, output_dir: str, interactive: bool = False):
    # Find all SKILL.md files recursively
    skill_files = glob.glob(os.path.join(input_dir, "**/SKILL.md"), recursive=True)

    if not skill_files:
        print(f"No SKILL.md files found in {input_dir}")
        return

    print(f"Found {len(skill_files)} skills to convert.")

    converter = SkillConverter()
    for skill_file in skill_files:
        print(f"\nProcessing: {skill_file}")
        skill_name = _skill_name_from_path(skill_file, input_dir)


        with open(skill_file, "r") as f:
            content = f.read()

        manus_content, report = converter.convert(
            content,
            interactive=interactive,
            on_unresolved_tool=on_unresolved_tool_cli if interactive else None
        )

        output_skill_dir = os.path.join(output_dir, skill_name)
        save_conversion_results(output_skill_dir, skill_name, manus_content, report, skill_file)
        print(f"Converted {skill_name} to {output_skill_dir}")

def fetch_and_convert_skill(skill_identifier: str, output_dir: str, interactive: bool = False):
    converter = SkillConverter()
    fetcher = SkillFetcher()


    print(f"Attempting to fetch skill: {skill_identifier}")
    clawhub_skill_content, skill_name = fetcher.fetch_skill(skill_identifier)

    if not clawhub_skill_content:
        print(f"Error: Could not fetch skill '{skill_identifier}'. Please check the identifier or URL.")
        return
    
    if not skill_name:
        # Derive a name if not explicitly found during fetch
        skill_name = skill_identifier.split("/")[-1].replace(".md", "").replace("SKILL", "").strip("-")
        if not skill_name:
            skill_name = "fetched-skill"
    skill_name = _safe_dir_name(skill_name)

    manus_skill_content, report = converter.convert(
        clawhub_skill_content,
        interactive=interactive,
        on_unresolved_tool=on_unresolved_tool_cli if interactive else None
    )

    _print_conversion_report(report)

    output_skill_dir = os.path.join(output_dir, skill_name)
    save_conversion_results(output_skill_dir, skill_name, manus_skill_content, report)
    print(f"\nFetched and converted skill saved to: {output_skill_dir}")

def validate_skill(skill_path: str):
    if not os.path.exists(skill_path):
        print(f"Error: Skill file not found at {skill_path}")
        return

    # If a directory is given, resolve to SKILL.md inside it
    if os.path.isdir(skill_path):
        skill_path = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(skill_path):
            print(f"Error: No SKILL.md found in directory {skill_path}")
            return

    with open(skill_path, "r") as f:
        skill_content = f.read()

    errors = ManusSkillValidator.validate_manus_skill(skill_content)

    if errors:
        print(f"\n--- Validation Errors for {skill_path} ---")
        for error in errors:
            print(f"- {error}")
        print("------------------------------------------")
    else:
        print(f"\nSkill {skill_path} is valid according to Manus requirements.")

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    parser = argparse.ArgumentParser(description="Convert ClawHub SKILL.md to Manus-compatible skills.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert a local ClawHub SKILL.md file.")
    convert_parser.add_argument("input_path", help="Path to the ClawHub SKILL.md file.")
    convert_parser.add_argument("--output", "-o", default=".", help="Output directory for the converted skill.")
    convert_parser.add_argument("--dry-run", action="store_true", help="Show conversion report and output without saving.")
    convert_parser.add_argument("--diff", action="store_true", dest="show_diff", help="Show a unified diff between input and output (in addition to the report).")
    convert_parser.add_argument("--interactive", "-i", action="store_true", help="Enable interactive tool mapping.")
    convert_parser.set_defaults(func=lambda args: convert_skill(args.input_path, args.output, args.dry_run, args.interactive, args.show_diff))

    # Convert-all command
    convert_all_parser = subparsers.add_parser("convert-all", help="Convert all SKILL.md files in a directory.")
    convert_all_parser.add_argument("input_dir", help="Directory to search for SKILL.md files.")
    convert_all_parser.add_argument("--output", "-o", default="converted_skills", help="Output directory.")
    convert_all_parser.add_argument("--interactive", "-i", action="store_true", help="Enable interactive tool mapping.")
    convert_all_parser.set_defaults(func=lambda args: convert_all_skills(args.input_dir, args.output, args.interactive))

    # Fetch-and-convert command
    fetch_parser = subparsers.add_parser("fetch-and-convert", help="Fetch a skill from ClawHub and convert it.")
    fetch_parser.add_argument("skill_identifier", help="Skill name or full GitHub raw URL.")
    fetch_parser.add_argument("--output", "-o", default=".", help="Output directory.")
    fetch_parser.add_argument("--interactive", "-i", action="store_true", help="Enable interactive tool mapping.")
    fetch_parser.set_defaults(func=lambda args: fetch_and_convert_skill(args.skill_identifier, args.output, args.interactive))

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an existing Manus SKILL.md file.")
    validate_parser.add_argument("skill_path", help="Path to the Manus SKILL.md file or directory containing it.")
    validate_parser.set_defaults(func=lambda args: validate_skill(args.skill_path))

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
