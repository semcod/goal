#!/usr/bin/env python3
"""
Template generator for Goal projects.

Quickly scaffold new projects with Goal pre-configured.
"""

import sys
import os
import argparse
from pathlib import Path


TEMPLATES = {
    "python": {
        "name": "Python Package",
        "files": {
            "pyproject.toml": '''[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
authors = [{name = "{author}", email = "{email}"}]
license = "{license}"
readme = "README.md"
requires-python = ">=3.8"

[project.optional-dependencies]
dev = ["pytest", "goal>=2.1.0"]

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
''',
            "src/{project_name}/__init__.py": '''"""{description}"""

__version__ = "0.1.0"
''',
            "tests/test_{project_name}.py": '''def test_example():
    assert True
''',
            "goal.yaml": '''version: "1.0"

project:
  name: "{project_name}"
  type: "python"
  versioning:
    strategy: "semantic"

commit:
  conventional:
    enabled: true

testing:
  command: "pytest tests/ -v"

publishing:
  enabled: true
'''
        }
    },
    
    "nodejs": {
        "name": "Node.js Application",
        "files": {
            "package.json": '''{{
  "name": "{project_name}",
  "version": "0.1.0",
  "description": "{description}",
  "main": "index.js",
  "scripts": {{
    "test": "jest",
    "start": "node index.js"
  }},
  "devDependencies": {{
    "jest": "^29.0.0",
    "goal": "^2.1.0"
  }}
}}
''',
            "index.js": '''console.log("Hello from {project_name}!");
''',
            "index.test.js": '''test('example', () => {
  expect(true).toBe(true);
});
''',
            "goal.yaml": '''version: "1.0"

project:
  name: "{project_name}"
  type: "nodejs"

testing:
  command: "npm test"
'''
        }
    },
    
    "rust": {
        "name": "Rust Crate",
        "files": {
            "Cargo.toml": '''[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"
description = "{description}"
license = "{license}"

[dependencies]
''',
            "src/lib.rs": '''//! {description}

pub fn hello() -> &'static str {{
    "Hello from {project_name}!"
}}
''',
            "src/main.rs": '''fn main() {{
    println!("Hello from {project_name}!");
}}
''',
            "goal.yaml": '''version: "1.0"

project:
  name: "{project_name}"
  type: "rust"

testing:
  command: "cargo test"
'''
        }
    },
    
    "go": {
        "name": "Go Module",
        "files": {
            "go.mod": '''module github.com/{author}/{project_name}

go 1.21
''',
            "main.go": '''package main

import "fmt"

func main() {{
    fmt.Println("Hello from {project_name}!")
}}
''',
            "{project_name}_test.go": '''package main

import "testing"

func TestHello(t *testing.T) {{
    // Test logic here
}}
''',
            "goal.yaml": '''version: "1.0"

project:
  name: "{project_name}"
  type: "go"

testing:
  command: "go test ./..."
'''
        }
    }
}


def generate_project(template_type, project_name, **kwargs):
    """Generate project from template."""
    if template_type not in TEMPLATES:
        print(f"✗ Unknown template: {template_type}")
        print(f"Available: {', '.join(TEMPLATES.keys())}")
        return False
    
    template = TEMPLATES[template_type]
    
    # Create project directory
    project_dir = Path(project_name)
    if project_dir.exists():
        print(f"✗ Directory already exists: {project_name}")
        return False
    
    project_dir.mkdir(parents=True)
    
    # Prepare template variables
    variables = {
        "project_name": project_name,
        "description": kwargs.get("description", f"A {template['name']} project"),
        "author": kwargs.get("author", "Your Name"),
        "email": kwargs.get("email", "you@example.com"),
        "license": kwargs.get("license", "MIT"),
    }
    
    # Generate files
    for file_path_template, content_template in template["files"].items():
        file_path = file_path_template.format(**variables)
        full_path = project_dir / file_path
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        content = content_template.format(**variables)
        full_path.write_text(content)
        print(f"  ✓ Created {file_path}")
    
    print(f"\n✅ Project '{project_name}' created!")
    print(f"\nNext steps:")
    print(f"  cd {project_name}")
    print(f"  goal init")
    print(f"  goal --all")
    
    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Goal project templates"
    )
    parser.add_argument(
        "template",
        choices=list(TEMPLATES.keys()),
        help="Project template type"
    )
    parser.add_argument(
        "name",
        help="Project name"
    )
    parser.add_argument(
        "--description", "-d",
        default=None,
        help="Project description"
    )
    parser.add_argument(
        "--author", "-a",
        default="Your Name",
        help="Author name"
    )
    parser.add_argument(
        "--email", "-e",
        default="you@example.com",
        help="Author email"
    )
    parser.add_argument(
        "--license", "-l",
        default="MIT",
        help="License type"
    )
    
    args = parser.parse_args()
    
    success = generate_project(
        args.template,
        args.name,
        description=args.description,
        author=args.author,
        email=args.email,
        license=args.license
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
