#!/usr/bin/env python3
"""
Syntax checker for all example files.

Validates:
- Python syntax (py_compile)
- Shell script syntax (bash -n)
- JSON validity
- YAML validity (if PyYAML available)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class SyntaxChecker:
    """Checks syntax of various file types."""

    def __init__(self, goal_root: Path):
        self.goal_root = goal_root
        self.errors: List[Tuple[Path, str, str]] = []

    def check_python(self, file_path: Path) -> bool:
        """Check Python syntax using py_compile."""
        try:
            import py_compile

            py_compile.compile(str(file_path), doraise=True)
            return True
        except Exception as e:
            self.errors.append((file_path, "PYTHON_SYNTAX", str(e)))
            return False

    def check_shell(self, file_path: Path) -> bool:
        """Check shell script syntax using bash -n."""
        try:
            result = subprocess.run(
                ["bash", "-n", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                self.errors.append(
                    (file_path, "SHELL_SYNTAX", result.stderr or "Syntax error")
                )
                return False
            return True
        except subprocess.TimeoutExpired:
            self.errors.append((file_path, "SHELL_SYNTAX", "Timeout"))
            return False
        except FileNotFoundError:
            # bash not available, skip
            return True
        except Exception as e:
            self.errors.append((file_path, "SHELL_SYNTAX", str(e)))
            return False

    def check_json(self, file_path: Path) -> bool:
        """Check JSON validity."""
        try:
            content = file_path.read_text(encoding="utf-8")
            json.loads(content)
            return True
        except json.JSONDecodeError as e:
            self.errors.append((file_path, "JSON_SYNTAX", str(e)))
            return False
        except Exception as e:
            self.errors.append((file_path, "JSON_READ", str(e)))
            return False

    def check_yaml(self, file_path: Path) -> bool:
        """Check YAML validity if PyYAML available."""
        try:
            import yaml

            content = file_path.read_text(encoding="utf-8")
            yaml.safe_load(content)
            return True
        except ImportError:
            # PyYAML not installed, skip
            return True
        except yaml.YAMLError as e:
            self.errors.append((file_path, "YAML_SYNTAX", str(e)))
            return False
        except Exception as e:
            self.errors.append((file_path, "YAML_READ", str(e)))
            return False

    def check_file(self, file_path: Path) -> bool:
        """Check a single file based on its extension."""
        suffix = file_path.suffix.lower()

        if suffix == ".py":
            return self.check_python(file_path)
        elif suffix == ".sh":
            return self.check_shell(file_path)
        elif suffix == ".json":
            return self.check_json(file_path)
        elif suffix in (".yaml", ".yml"):
            return self.check_yaml(file_path)
        elif suffix in (".toml", ".ini", ".cfg"):
            # These are typically valid if readable
            try:
                file_path.read_text(encoding="utf-8")
                return True
            except Exception as e:
                self.errors.append((file_path, "READ_ERROR", str(e)))
                return False
        else:
            # Unknown type, skip
            return True

    def check_all_examples(self) -> bool:
        """Check all relevant files in examples directory."""
        examples_dir = self.goal_root / "examples"

        if not examples_dir.exists():
            print(f"❌ Examples directory not found: {examples_dir}")
            return False

        # Find all checkable files
        checkable_extensions = {".py", ".sh", ".json", ".yaml", ".yml", ".toml"}
        files = []
        for ext in checkable_extensions:
            files.extend(examples_dir.rglob(f"*{ext}"))

        print(f"Found {len(files)} files to check\n")

        all_valid = True
        stats = {"python": 0, "shell": 0, "json": 0, "yaml": 0, "toml": 0}

        for file_path in sorted(files):
            # Skip __pycache__
            if "__pycache__" in str(file_path):
                continue

            suffix = file_path.suffix.lower()

            if suffix == ".py":
                stats["python"] += 1
                file_type = "Python"
            elif suffix == ".sh":
                stats["shell"] += 1
                file_type = "Shell"
            elif suffix == ".json":
                stats["json"] += 1
                file_type = "JSON"
            elif suffix in (".yaml", ".yml"):
                stats["yaml"] += 1
                file_type = "YAML"
            elif suffix == ".toml":
                stats["toml"] += 1
                file_type = "TOML"
            else:
                continue

            print(f"Checking {file_type}: {file_path.relative_to(self.goal_root)}...")
            if not self.check_file(file_path):
                all_valid = False

        print(f"\nStats: {stats}")
        return all_valid

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("SYNTAX CHECK REPORT")
        print("=" * 70)

        if not self.errors:
            print("\n✅ All files have valid syntax!")
            return

        by_file = {}
        for file_path, error_type, message in self.errors:
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append((error_type, message))

        print(f"\n❌ Found {len(self.errors)} syntax errors in {len(by_file)} files:\n")

        for file_path, errors in sorted(by_file.items()):
            print(f"\n{file_path.relative_to(self.goal_root)}:")
            for error_type, message in errors:
                print(f"  🔴 [{error_type}] {message}")


def main():
    """Run syntax check validation."""
    script_dir = Path(__file__).parent
    goal_root = script_dir.parent.parent

    print("=" * 70)
    print("Syntax Checker")
    print("=" * 70)
    print(f"Goal root: {goal_root}")
    print()

    checker = SyntaxChecker(goal_root)
    valid = checker.check_all_examples()
    checker.print_report()

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
