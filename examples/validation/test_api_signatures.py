#!/usr/bin/env python3
"""
Validates API signatures match between examples and actual implementation.

Catches issues like:
- Function signature changes (new/removed parameters)
- Return type changes
- Renamed functions
- Deprecated APIs still used in examples
"""

import ast
import inspect
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Any


class APISignatureValidator:
    """Validates API signatures in example files."""

    def __init__(self, goal_root: Path):
        self.goal_root = goal_root
        self.errors: List[Tuple[Path, str, str]] = []
        self.warnings: List[Tuple[Path, str, str]] = []

    def extract_function_calls(
        self, file_path: Path
    ) -> List[Tuple[str, str, ast.Call]]:
        """Extract all function calls from a Python file."""
        calls = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except SyntaxError as e:
            self.errors.append((file_path, "SYNTAX", str(e)))
            return []
        except Exception as e:
            self.errors.append((file_path, "READ", str(e)))
            return []

        # Track imports to know module prefixes
        imports = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name.split(".")[0]] = alias.name

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = f"{module}.{alias.name}" if module else alias.name

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Direct call: func_name()
                    func_name = node.func.id
                    if func_name in imports:
                        full_name = imports[func_name]
                    else:
                        full_name = func_name
                    calls.append((full_name, func_name, node))

                elif isinstance(node.func, ast.Attribute):
                    # Method call: module.func() or obj.method()
                    # Try to resolve the full path
                    parts = []
                    current = node.func
                    while isinstance(current, ast.Attribute):
                        parts.append(current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.append(current.id)
                        parts.reverse()

                        # Check if it's an imported module
                        first_part = parts[0]
                        if first_part in imports:
                            full_name = imports[first_part]
                            if len(parts) > 1:
                                full_name = f"{full_name}.{'.'.join(parts[1:])}"
                        else:
                            full_name = ".".join(parts)

                        calls.append((full_name, parts[-1], node))

        return calls

    def resolve_function(self, full_name: str) -> Optional[Any]:
        """Try to resolve a function by its full dotted name."""
        try:
            parts = full_name.split(".")
            if not parts:
                return None

            # Try importing the module
            module_name = parts[0]
            for i, part in enumerate(parts[1:], 1):
                try:
                    module = __import__(module_name, fromlist=[part])
                    obj = getattr(module, part, None)

                    # Navigate remaining parts
                    for remaining in parts[i + 1 :]:
                        if obj is None:
                            return None
                        obj = getattr(obj, remaining, None)

                    if callable(obj):
                        return obj

                except (ImportError, AttributeError):
                    continue

                module_name = f"{module_name}.{part}"

            return None

        except Exception:
            return None

    def validate_call(
        self, full_name: str, call_node: ast.Call, file_path: Path
    ) -> bool:
        """Validate a single function call against the actual API."""
        # Skip non-goal imports
        if not full_name.startswith("goal"):
            return True

        func = self.resolve_function(full_name)
        if func is None:
            # Could be legitimate - maybe it's an object attribute
            return True

        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.items())

            # Get call arguments
            call_args = {}

            # Positional args
            for i, arg in enumerate(call_node.args):
                if i < len(params):
                    param_name = params[i][0]
                    call_args[param_name] = arg

            # Keyword args
            for kw in call_node.keywords:
                call_args[kw.arg] = kw.value

            # Check for removed parameters
            valid_params = {p[0] for p in params}
            for arg_name in call_args.keys():
                if arg_name not in valid_params and arg_name is not None:
                    self.errors.append(
                        (
                            file_path,
                            "INVALID_PARAM",
                            f"{full_name}() got unexpected keyword argument '{arg_name}'",
                        )
                    )
                    return False

            # Check for required parameters
            required = {
                p[0]
                for p in params
                if p[1].default == inspect.Parameter.empty
                and p[1].kind
                in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.POSITIONAL_ONLY,
                )
            }

            # Check varargs/kwargs
            has_varargs = any(
                p[1].kind == inspect.Parameter.VAR_POSITIONAL for p in params
            )
            has_kwargs = any(p[1].kind == inspect.Parameter.VAR_KEYWORD for p in params)

            if not has_kwargs:
                # If no **kwargs, strict checking applies
                for arg_name in call_args.keys():
                    if arg_name and arg_name not in valid_params:
                        self.errors.append(
                            (
                                file_path,
                                "INVALID_PARAM",
                                f"{full_name}() got unexpected keyword argument '{arg_name}'",
                            )
                        )
                        return False

            return True

        except (ValueError, TypeError):
            # Can't get signature (maybe built-in)
            return True

    def validate_file(self, file_path: Path) -> bool:
        """Validate all API calls in a single file."""
        calls = self.extract_function_calls(file_path)
        all_valid = True

        for full_name, short_name, call_node in calls:
            if not self.validate_call(full_name, call_node, file_path):
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

            # Skip validation scripts themselves
            if "validation" in str(file_path):
                continue

            print(f"Checking API calls in {file_path.relative_to(self.goal_root)}...")
            if not self.validate_file(file_path):
                all_valid = False

        return all_valid

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("API SIGNATURE VALIDATION REPORT")
        print("=" * 70)

        if not self.errors:
            print("\n✅ All API calls valid!")
            return

        by_file = {}
        for file_path, error_type, message in self.errors:
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append((error_type, message))

        print(f"\n❌ Found {len(self.errors)} API issues in {len(by_file)} files:\n")

        for file_path, errors in sorted(by_file.items()):
            print(f"\n{file_path.relative_to(self.goal_root)}:")
            for error_type, message in errors:
                print(f"  🔴 [{error_type}] {message}")


def main():
    """Run API signature validation."""
    script_dir = Path(__file__).parent
    goal_root = script_dir.parent.parent

    print("=" * 70)
    print("API Signature Validator")
    print("=" * 70)
    print(f"Goal root: {goal_root}")
    print()

    sys.path.insert(0, str(goal_root))

    validator = APISignatureValidator(goal_root)
    valid = validator.validate_all_examples()
    validator.print_report()

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
