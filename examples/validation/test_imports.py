#!/usr/bin/env python3
"""
Validates all imports in example files actually work.

This catches issues like:
- Importing non-existent modules
- Importing non-existent functions/classes
- Broken API paths after refactoring
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class ImportValidator:
    """Validates imports in Python files."""

    def __init__(self, goal_root: Path):
        self.goal_root = goal_root
        self.errors: List[Tuple[Path, str, str]] = []
        self.warnings: List[Tuple[Path, str, str]] = []

    def extract_imports(self, file_path: Path) -> List[Tuple[str, Optional[List[str]]]]:
        """Extract all imports from a Python file."""
        imports = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except SyntaxError as e:
            self.errors.append((file_path, "SYNTAX", str(e)))
            return []
        except Exception as e:
            self.errors.append((file_path, "READ", str(e)))
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, None))

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append((module, names))

        return imports

    def validate_import(
        self, module: str, names: Optional[List[str]], file_path: Path
    ) -> bool:
        """Validate a single import."""
        # Skip standard library and third-party
        stdlib_modules = {
            "os",
            "sys",
            "pathlib",
            "tempfile",
            "subprocess",
            "json",
            "re",
            "datetime",
            "time",
            "typing",
            "collections",
            "contextlib",
            "unittest",
            "unittest.mock",
            "urllib",
            "urllib.request",
            "inspect",
            "importlib",
            "argparse",
            "logging",
            "traceback",
            "importlib.metadata",
            "tomllib",
        }

        if module.split(".")[0] in stdlib_modules:
            return True

        # Skip third-party
        third_party = {"click", "git", "requests", "yaml", "pytest"}
        if module.split(".")[0] in third_party:
            return True

        # Check if it's a goal import
        if not module.startswith("goal"):
            return True

        # Try to import
        try:
            if names:
                # from goal.x import y
                mod = __import__(module, fromlist=names)
                for name in names:
                    if not hasattr(mod, name):
                        self.errors.append(
                            (
                                file_path,
                                "MISSING_ATTR",
                                f"{module}.{name} does not exist",
                            )
                        )
                        return False
            else:
                # import goal.x
                __import__(module)

            return True

        except ImportError as e:
            self.errors.append((file_path, "IMPORT", f"Cannot import {module}: {e}"))
            return False
        except Exception as e:
            self.errors.append((file_path, "ERROR", f"Error importing {module}: {e}"))
            return False

    def validate_file(self, file_path: Path) -> bool:
        """Validate all imports in a single file."""
        imports = self.extract_imports(file_path)
        all_valid = True

        for module, names in imports:
            if not self.validate_import(module, names, file_path):
                all_valid = False

        return all_valid

    def validate_all_examples(self) -> bool:
        """Validate all Python files in examples directory."""
        examples_dir = self.goal_root / "examples"

        if not examples_dir.exists():
            print(f"❌ Examples directory not found: {examples_dir}")
            return False

        python_files = list(examples_dir.rglob("*.py"))

        print(f"Found {len(python_files)} Python files to validate\n")

        all_valid = True
        for file_path in sorted(python_files):
            # Skip __pycache__
            if "__pycache__" in str(file_path):
                continue

            print(f"Checking {file_path.relative_to(self.goal_root)}...")
            if not self.validate_file(file_path):
                all_valid = False

        return all_valid

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("IMPORT VALIDATION REPORT")
        print("=" * 70)

        if not self.errors:
            print("\n✅ All imports valid!")
            return

        # Group by file
        by_file = {}
        for file_path, error_type, message in self.errors:
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append((error_type, message))

        print(f"\n❌ Found {len(self.errors)} import errors in {len(by_file)} files:\n")

        for file_path, errors in sorted(by_file.items()):
            print(f"\n{file_path.relative_to(self.goal_root)}:")
            for error_type, message in errors:
                icon = "🔴" if error_type in ("IMPORT", "MISSING_ATTR") else "🟡"
                print(f"  {icon} [{error_type}] {message}")


def main():
    """Run import validation."""
    # Find goal root
    script_dir = Path(__file__).parent
    goal_root = script_dir.parent.parent  # examples/validation/ -> examples/ -> goal/

    print("=" * 70)
    print("Example Import Validator")
    print("=" * 70)
    print(f"Goal root: {goal_root}")
    print()

    # Add goal to path
    sys.path.insert(0, str(goal_root))

    validator = ImportValidator(goal_root)
    valid = validator.validate_all_examples()
    validator.print_report()

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
