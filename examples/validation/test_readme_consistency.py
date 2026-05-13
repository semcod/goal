#!/usr/bin/env python3
"""
Validates README files accurately describe the examples directory.

Catches issues like:
- Referenced files that don't exist
- Listed directories that don't exist
- Outdated directory structures
- Missing new examples
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Set, Dict


class READMEConsistencyValidator:
    """Validates README consistency with actual directory structure."""

    def __init__(self, goal_root: Path):
        self.goal_root = goal_root
        self.errors: List[Tuple[Path, str, str]] = []
        self.warnings: List[Tuple[Path, str, str]] = []

    def extract_file_references(self, readme_content: str) -> Set[str]:
        """Extract file/directory references from markdown content."""
        references = set()

        # Match file references in backticks: `file.py`
        for match in re.finditer(r"`([^`]+\.py)`", readme_content):
            references.add(match.group(1))

        # Match file references in code blocks
        for match in re.finditer(
            r"```\w*\n.*?(\S+\.py).*?```", readme_content, re.DOTALL
        ):
            references.add(match.group(1))

        # Match directory references in tree structures
        for match in re.finditer(
            r"^(?:├──|└──|│\s+)([\w\-]+/)", readme_content, re.MULTILINE
        ):
            references.add(match.group(1))

        # Match path references: examples/xxx/yyy
        for match in re.finditer(
            r"examples/([\w\-/]+\.(?:py|md|json|toml|yaml))", readme_content
        ):
            references.add(match.group(1))

        # Match mention of directories ending with /
        for match in re.finditer(r"`([\w\-]+/)`", readme_content):
            references.add(match.group(1))

        return references

    def extract_markdown_links(self, readme_content: str) -> List[Tuple[str, str]]:
        """Extract markdown links [text](path)."""
        links = []
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", readme_content):
            text = match.group(1)
            path = match.group(2)
            links.append((text, path))
        return links

    def get_actual_structure(self, examples_dir: Path) -> Dict[str, List[str]]:
        """Get actual directory structure."""
        structure = {"files": [], "dirs": [], "py_files": [], "md_files": []}

        if not examples_dir.exists():
            return structure

        for item in examples_dir.rglob("*"):
            # Skip __pycache__ and hidden
            if "__pycache__" in str(item) or item.name.startswith("."):
                continue

            relative = item.relative_to(examples_dir)
            path_str = str(relative)

            if item.is_file():
                structure["files"].append(path_str)
                if item.suffix == ".py":
                    structure["py_files"].append(path_str)
                elif item.suffix == ".md":
                    structure["md_files"].append(path_str)
            elif item.is_dir():
                structure["dirs"].append(path_str + "/")

        return structure

    def validate_readme(self, readme_path: Path, examples_dir: Path) -> bool:
        """Validate a single README file."""
        valid = True

        try:
            content = readme_path.read_text(encoding="utf-8")
        except Exception as e:
            self.errors.append((readme_path, "READ", str(e)))
            return False

        # Get actual structure
        structure = self.get_actual_structure(examples_dir)
        all_items = set(
            structure["files"]
            + structure["dirs"]
            + [d.rstrip("/") for d in structure["dirs"]]
        )

        # Check file references
        references = self.extract_file_references(content)
        for ref in references:
            # Normalize the reference
            ref_clean = ref.rstrip("/")

            # Check if it exists
            if ref_clean not in all_items and ref not in structure["dirs"]:
                # Check if it's just a basename that could exist anywhere
                if "/" not in ref:
                    if not any(
                        f.endswith("/" + ref) or f == ref for f in structure["files"]
                    ):
                        self.errors.append(
                            (
                                readme_path,
                                "MISSING_REF",
                                f"Referenced file/dir not found: '{ref}'",
                            )
                        )
                        valid = False
                else:
                    self.errors.append(
                        (
                            readme_path,
                            "MISSING_REF",
                            f"Referenced path not found: '{ref}'",
                        )
                    )
                    valid = False

        # Check markdown links
        links = self.extract_markdown_links(content)
        for text, path in links:
            # Skip URLs
            if path.startswith(("http://", "https://", "#")):
                continue

            # Check relative paths
            if path.startswith("../") or path.startswith("./"):
                resolved = readme_path.parent / path
                if not resolved.exists():
                    self.warnings.append(
                        (
                            readme_path,
                            "BROKEN_LINK",
                            f"Link may be broken: [{text}]({path})",
                        )
                    )

        # Check for documented but missing subdirectories
        documented_dirs = self.extract_documented_directories(content)
        actual_dirs = {d.rstrip("/") for d in structure["dirs"]}

        for doc_dir in documented_dirs:
            if doc_dir not in actual_dirs:
                self.errors.append(
                    (
                        readme_path,
                        "MISSING_DIR",
                        f"Documented directory not found: '{doc_dir}/'",
                    )
                )
                valid = False

        # Check for undocumented files (new examples not in README)
        if readme_path.name == "README.md":
            documented_files = self.extract_documented_files(content)
            for py_file in structure["py_files"]:
                basename = Path(py_file).name
                if basename not in documented_files and "test_" not in basename:
                    self.warnings.append(
                        (
                            readme_path,
                            "UNDOCUMENTED",
                            f"File not documented: '{py_file}'",
                        )
                    )

        return valid

    def extract_documented_directories(self, content: str) -> Set[str]:
        """Extract directory names mentioned in documentation."""
        dirs = set()

        # Look for patterns like "### 1. Directory Name" or "- Directory/"
        for match in re.finditer(r"###\s+\d+\.\s+([\w\-]+)", content):
            dirs.add(match.group(1).lower())

        for match in re.finditer(r"-\s+`?([\w\-]+)/`?", content):
            dirs.add(match.group(1).lower())

        return dirs

    def extract_documented_files(self, content: str) -> Set[str]:
        """Extract file names that are documented."""
        files = set()

        for match in re.finditer(r"`([^`]+\.py)`", content):
            files.add(match.group(1))

        return files

    def validate_all(self) -> bool:
        """Validate all README files."""
        examples_dir = self.goal_root / "examples"

        if not examples_dir.exists():
            print(f"❌ Examples directory not found: {examples_dir}")
            return False

        # Find all README files
        readme_files = list(examples_dir.rglob("README.md"))

        print(f"Found {len(readme_files)} README files to validate\n")

        all_valid = True
        for readme_path in sorted(readme_files):
            print(f"Checking {readme_path.relative_to(self.goal_root)}...")
            if not self.validate_readme(readme_path, examples_dir):
                all_valid = False

        return all_valid

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("README CONSISTENCY REPORT")
        print("=" * 70)

        if not self.errors and not self.warnings:
            print("\n✅ All README files consistent!")
            return

        # Group by file
        by_file_errors = {}
        for file_path, error_type, message in self.errors:
            if file_path not in by_file_errors:
                by_file_errors[file_path] = []
            by_file_errors[file_path].append((error_type, message))

        by_file_warnings = {}
        for file_path, error_type, message in self.warnings:
            if file_path not in by_file_warnings:
                by_file_warnings[file_path] = []
            by_file_warnings[file_path].append((error_type, message))

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} errors:\n")
            for file_path, errors in sorted(by_file_errors.items()):
                print(f"\n{file_path.relative_to(self.goal_root)}:")
                for error_type, message in errors:
                    print(f"  🔴 [{error_type}] {message}")

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:\n")
            for file_path, warnings in sorted(by_file_warnings.items()):
                print(f"\n{file_path.relative_to(self.goal_root)}:")
                for warning_type, message in warnings:
                    print(f"  🟡 [{warning_type}] {message}")


def main():
    """Run README consistency validation."""
    script_dir = Path(__file__).parent
    goal_root = script_dir.parent.parent

    print("=" * 70)
    print("README Consistency Validator")
    print("=" * 70)
    print(f"Goal root: {goal_root}")
    print()

    validator = READMEConsistencyValidator(goal_root)
    valid = validator.validate_all()
    validator.print_report()

    # Strict mode: fail on warnings too
    has_warnings = len(validator.warnings) > 0
    sys.exit(0 if valid and not has_warnings else 1)


if __name__ == "__main__":
    main()
