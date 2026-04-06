import argparse
import os
from claw2manus.converter import SkillConverter
from claw2manus.fetcher import SkillFetcher
from claw2manus.validators import ManusSkillValidator

def convert_skill(input_path: str, output_dir: str, dry_run: bool):
    converter = SkillConverter()
    
    with open(input_path, "r") as f:
        clawhub_skill_content = f.read()

    manus_skill_content, report = converter.convert(clawhub_skill_content)

    print("\n--- Conversion Report ---")
    if report:
        for item in report:
            print(f"- {item}")
    else:
        print("No specific changes noted during conversion (may still have implicit formatting changes).")
    print("-------------------------")

    if not dry_run:
        output_filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, output_filename)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(manus_skill_content)
        print(f"\nConverted skill saved to: {output_path}")
    else:
        print("\n--- Converted Skill (Dry Run) ---")
        print(manus_skill_content)
        print("---------------------------------")

def fetch_and_convert_skill(skill_identifier: str, output_dir: str):
    fetcher = SkillFetcher()
    converter = SkillConverter()

    print(f"Attempting to fetch skill: {skill_identifier}")
    clawhub_skill_content, skill_name = fetcher.fetch_skill(skill_identifier)

    if not clawhub_skill_content:
        print(f"Error: Could not fetch skill \'{skill_identifier}\'. Please check the identifier or URL.")
        return
    
    if not skill_name:
        # Derive a name if not explicitly found during fetch
        skill_name = skill_identifier.split("/")[-1].replace(".md", "").replace("SKILL", "").strip("-")
        if not skill_name:
            skill_name = "fetched-skill"

    manus_skill_content, report = converter.convert(clawhub_skill_content)

    print("\n--- Conversion Report ---")
    if report:
        for item in report:
            print(f"- {item}")
    else:
        print("No specific changes noted during conversion (may still have implicit formatting changes).")
    print("-------------------------")

    output_skill_dir = os.path.join(output_dir, skill_name)
    os.makedirs(output_skill_dir, exist_ok=True)
    output_path = os.path.join(output_skill_dir, "SKILL.md")
    with open(output_path, "w") as f:
        f.write(manus_skill_content)
    print(f"\nFetched and converted skill saved to: {output_path}")

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
    parser = argparse.ArgumentParser(description="Convert ClawHub SKILL.md to Manus-compatible skills.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert a local ClawHub SKILL.md file.")
    convert_parser.add_argument("input_path", help="Path to the ClawHub SKILL.md file.")
    convert_parser.add_argument("--output", "-o", default=".", help="Output directory for the converted skill. Defaults to current directory.")
    convert_parser.add_argument("--dry-run", action="store_true", help="Show conversion report and output without saving to file.")
    convert_parser.set_defaults(func=lambda args: convert_skill(args.input_path, args.output, args.dry_run))

    # Fetch-and-convert command
    fetch_parser = subparsers.add_parser("fetch-and-convert", help="Fetch a skill from ClawHub and convert it.")
    fetch_parser.add_argument("skill_identifier", help="Skill name (e.g., pwnclaw-security-scan) or full GitHub raw URL.")
    fetch_parser.add_argument("--output", "-o", default=".", help="Output directory for the converted skill. Defaults to current directory.")
    fetch_parser.set_defaults(func=lambda args: fetch_and_convert_skill(args.skill_identifier, args.output))

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an existing Manus SKILL.md file.")
    validate_parser.add_argument("skill_path", help="Path to the Manus SKILL.md file or directory containing it.")
    validate_parser.set_defaults(func=lambda args: validate_skill(args.skill_path))

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
