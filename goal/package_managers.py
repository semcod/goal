"""
Package Manager Detection and Management System

This module provides comprehensive support for multiple package managers
across different programming languages and ecosystems.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import re


@dataclass
class PackageManager:
    """Package manager configuration and capabilities."""
    name: str
    language: str
    lock_files: List[str]
    config_files: List[str]
    install_cmd: str
    add_cmd: str
    remove_cmd: str
    update_cmd: str
    test_cmd: Optional[str] = None
    publish_cmd: Optional[str] = None
    build_cmd: Optional[str] = None
    run_cmd: Optional[str] = None
    version_cmd: Optional[str] = None
    env_vars: Dict[str, str] = None
    priority: int = 1  # Higher priority = preferred choice
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


# Comprehensive package manager definitions
PACKAGE_MANAGERS: Dict[str, PackageManager] = {
    # Python Package Managers
    'poetry': PackageManager(
        name='poetry',
        language='python',
        lock_files=['poetry.lock'],
        config_files=['pyproject.toml'],
        install_cmd='poetry install',
        add_cmd='poetry add {package}',
        remove_cmd='poetry remove {package}',
        update_cmd='poetry update',
        test_cmd='poetry run pytest',
        publish_cmd='poetry publish',
        build_cmd='poetry build',
        run_cmd='poetry run {command}',
        version_cmd='poetry version',
        priority=10
    ),
    
    'uv': PackageManager(
        name='uv',
        language='python',
        lock_files=['uv.lock'],
        config_files=['pyproject.toml'],
        install_cmd='uv sync',
        add_cmd='uv add {package}',
        remove_cmd='uv remove {package}',
        update_cmd='uv sync --upgrade',
        test_cmd='uv run pytest',
        publish_cmd='uv publish',
        build_cmd='uv build',
        run_cmd='uv run {command}',
        version_cmd='uv version',
        priority=9  # Very high priority, modern tool
    ),
    
    'pip': PackageManager(
        name='pip',
        language='python',
        lock_files=['requirements.txt', 'requirements-dev.txt'],
        config_files=['setup.py', 'setup.cfg', 'pyproject.toml'],
        install_cmd='pip install -r requirements.txt',
        add_cmd='pip install {package}',
        remove_cmd='pip uninstall {package}',
        update_cmd='pip install --upgrade {package}',
        test_cmd='pytest',
        build_cmd='python -m build',
        publish_cmd='python -m twine upload dist/*',
        run_cmd='python {command}',
        version_cmd='python setup.py --version',
        priority=1
    ),
    
    'conda': PackageManager(
        name='conda',
        language='python',
        lock_files=['environment.yml', 'conda-lock.yml'],
        config_files=['environment.yml'],
        install_cmd='conda env create -f environment.yml',
        add_cmd='conda install {package}',
        remove_cmd='conda remove {package}',
        update_cmd='conda update {package}',
        test_cmd='pytest',
        build_cmd='python -m build',
        publish_cmd='anaconda upload',
        run_cmd='conda run {command}',
        version_cmd='conda list',
        env_vars={'CONDA_DEFAULT_ENV': 'base'},
        priority=8
    ),
    
    'pipenv': PackageManager(
        name='pipenv',
        language='python',
        lock_files=['Pipfile.lock'],
        config_files=['Pipfile'],
        install_cmd='pipenv install',
        add_cmd='pipenv install {package}',
        remove_cmd='pipenv uninstall {package}',
        update_cmd='pipenv update',
        test_cmd='pipenv run pytest',
        build_cmd='pipenv run python -m build',
        publish_cmd='pipenv run python -m twine upload dist/*',
        run_cmd='pipenv run {command}',
        version_cmd='pipenv --version',
        priority=6
    ),
    
    # Node.js Package Managers
    'npm': PackageManager(
        name='npm',
        language='nodejs',
        lock_files=['package-lock.json'],
        config_files=['package.json'],
        install_cmd='npm install',
        add_cmd='npm install {package}',
        remove_cmd='npm uninstall {package}',
        update_cmd='npm update',
        test_cmd='npm test',
        publish_cmd='npm publish',
        build_cmd='npm run build',
        run_cmd='npm run {command}',
        version_cmd='npm --version',
        priority=5
    ),
    
    'yarn': PackageManager(
        name='yarn',
        language='nodejs',
        lock_files=['yarn.lock'],
        config_files=['package.json'],
        install_cmd='yarn install',
        add_cmd='yarn add {package}',
        remove_cmd='yarn remove {package}',
        update_cmd='yarn upgrade',
        test_cmd='yarn test',
        publish_cmd='yarn publish',
        build_cmd='yarn build',
        run_cmd='yarn {command}',
        version_cmd='yarn --version',
        priority=7
    ),
    
    'pnpm': PackageManager(
        name='pnpm',
        language='nodejs',
        lock_files=['pnpm-lock.yaml'],
        config_files=['package.json'],
        install_cmd='pnpm install',
        add_cmd='pnpm add {package}',
        remove_cmd='pnpm remove {package}',
        update_cmd='pnpm update',
        test_cmd='pnpm test',
        publish_cmd='pnpm publish',
        build_cmd='pnpm build',
        run_cmd='pnpm {command}',
        version_cmd='pnpm --version',
        priority=8
    ),
    
    'bun': PackageManager(
        name='bun',
        language='nodejs',
        lock_files=['bun.lockb'],
        config_files=['package.json'],
        install_cmd='bun install',
        add_cmd='bun add {package}',
        remove_cmd='bun remove {package}',
        update_cmd='bun update',
        test_cmd='bun test',
        publish_cmd='bun publish',
        build_cmd='bun build',
        run_cmd='bun {command}',
        version_cmd='bun --version',
        priority=9  # Very fast, modern
    ),
    
    # Rust Package Manager
    'cargo': PackageManager(
        name='cargo',
        language='rust',
        lock_files=['Cargo.lock'],
        config_files=['Cargo.toml'],
        install_cmd='cargo build',
        add_cmd='cargo add {package}',
        remove_cmd='cargo remove {package}',
        update_cmd='cargo update',
        test_cmd='cargo test',
        publish_cmd='cargo publish',
        build_cmd='cargo build --release',
        run_cmd='cargo run',
        version_cmd='cargo --version',
        priority=10
    ),
    
    # Go Package Manager
    'go': PackageManager(
        name='go',
        language='go',
        lock_files=['go.sum'],
        config_files=['go.mod', 'go.sum'],
        install_cmd='go mod download',
        add_cmd='go get {package}',
        remove_cmd='go mod tidy && go mod tidy -compat={package}',
        update_cmd='go get -u {package}',
        test_cmd='go test ./...',
        publish_cmd='git push origin --tags',
        build_cmd='go build',
        run_cmd='go run',
        version_cmd='go version',
        priority=10
    ),
    
    # Ruby Package Managers
    'bundler': PackageManager(
        name='bundler',
        language='ruby',
        lock_files=['Gemfile.lock'],
        config_files=['Gemfile'],
        install_cmd='bundle install',
        add_cmd='bundle add {package}',
        remove_cmd='bundle remove {package}',
        update_cmd='bundle update',
        test_cmd='bundle exec rspec',
        publish_cmd='gem build *.gemspec && gem push *.gem',
        build_cmd='bundle exec rake build',
        run_cmd='bundle exec {command}',
        version_cmd='bundle --version',
        priority=8
    ),
    
    'gem': PackageManager(
        name='gem',
        language='ruby',
        lock_files=[],
        config_files=['*.gemspec'],
        install_cmd='gem install',
        add_cmd='gem install {package}',
        remove_cmd='gem uninstall {package}',
        update_cmd='gem update {package}',
        test_cmd='rspec',
        publish_cmd='gem push *.gem',
        build_cmd='gem build *.gemspec',
        run_cmd='ruby {command}',
        version_cmd='gem --version',
        priority=5
    ),
    
    # PHP Package Manager
    'composer': PackageManager(
        name='composer',
        language='php',
        lock_files=['composer.lock'],
        config_files=['composer.json'],
        install_cmd='composer install',
        add_cmd='composer require {package}',
        remove_cmd='composer remove {package}',
        update_cmd='composer update',
        test_cmd='composer test',
        publish_cmd='composer publish',
        build_cmd='composer build',
        run_cmd='composer run {command}',
        version_cmd='composer --version',
        priority=10
    ),
    
    # Java Package Managers
    'maven': PackageManager(
        name='maven',
        language='java',
        lock_files=[],
        config_files=['pom.xml'],
        install_cmd='mvn install',
        add_cmd='mvn dependency:add -Dartifact={package}',
        remove_cmd='mvn dependency:purge-local-repository',
        update_cmd='mvn dependency:update',
        test_cmd='mvn test',
        publish_cmd='mvn deploy',
        build_cmd='mvn package',
        run_cmd='mvn exec:java',
        version_cmd='mvn --version',
        priority=8
    ),
    
    'gradle': PackageManager(
        name='gradle',
        language='java',
        lock_files=[],
        config_files=['build.gradle', 'build.gradle.kts'],
        install_cmd='gradle build',
        add_cmd='gradle add dependency {package}',
        remove_cmd='gradle remove dependency {package}',
        update_cmd='gradle dependency update',
        test_cmd='gradle test',
        publish_cmd='gradle publish',
        build_cmd='gradle build',
        run_cmd='gradle run',
        version_cmd='gradle --version',
        priority=9
    ),
    
    # .NET Package Manager
    'nuget': PackageManager(
        name='nuget',
        language='dotnet',
        lock_files=['packages.lock.json'],
        config_files=['*.csproj', '*.fsproj', 'packages.config'],
        install_cmd='dotnet restore',
        add_cmd='dotnet add package {package}',
        remove_cmd='dotnet remove package {package}',
        update_cmd='dotnet add package {package} --version latest',
        test_cmd='dotnet test',
        publish_cmd='dotnet nuget push *.nupkg',
        build_cmd='dotnet pack',
        run_cmd='dotnet run',
        version_cmd='dotnet --version',
        priority=8
    ),
    
    # Elixir Package Manager
    'mix': PackageManager(
        name='mix',
        language='elixir',
        lock_files=['mix.lock'],
        config_files=['mix.exs'],
        install_cmd='mix deps.get',
        add_cmd='mix deps.add {package}',
        remove_cmd='mix deps.remove {package}',
        update_cmd='mix deps.update',
        test_cmd='mix test',
        publish_cmd='mix hex.publish',
        build_cmd='mix compile',
        run_cmd='mix run',
        version_cmd='mix --version',
        priority=10
    ),
    
    # Haskell Package Manager
    'cabal': PackageManager(
        name='cabal',
        language='haskell',
        lock_files=['cabal.project.freeze'],
        config_files=['cabal.project', '*.cabal'],
        install_cmd='cabal build all',
        add_cmd='cabal add {package}',
        remove_cmd='cabal uninstall {package}',
        update_cmd='cabal update',
        test_cmd='cabal test',
        publish_cmd='cabal sdist',
        build_cmd='cabal build',
        run_cmd='cabal run',
        version_cmd='cabal --version',
        priority=7
    ),
    
    'stack': PackageManager(
        name='stack',
        language='haskell',
        lock_files=['stack.yaml.lock'],
        config_files=['stack.yaml'],
        install_cmd='stack build',
        add_cmd='stack add {package}',
        remove_cmd='stack uninstall {package}',
        update_cmd='stack update',
        test_cmd='stack test',
        publish_cmd='stack sdist',
        build_cmd='stack build',
        run_cmd='stack exec',
        version_cmd='stack --version',
        priority=8
    ),
    
    # Swift Package Manager
    'swift': PackageManager(
        name='swift',
        language='swift',
        lock_files=['Package.resolved'],
        config_files=['Package.swift'],
        install_cmd='swift package resolve',
        add_cmd='swift package add dependency {package}',
        remove_cmd='swift package remove dependency {package}',
        update_cmd='swift package update',
        test_cmd='swift test',
        publish_cmd='swift package publish',
        build_cmd='swift build',
        run_cmd='swift run',
        version_cmd='swift --version',
        priority=10
    ),
    
    # Dart Package Manager
    'pub': PackageManager(
        name='pub',
        language='dart',
        lock_files=['pubspec.lock'],
        config_files=['pubspec.yaml'],
        install_cmd='pub get',
        add_cmd='pub add {package}',
        remove_cmd='pub remove {package}',
        update_cmd='pub upgrade',
        test_cmd='dart test',
        publish_cmd='pub publish',
        build_cmd='dart compile',
        run_cmd='dart run',
        version_cmd='dart --version',
        priority=10
    ),
    
    # Kotlin Package Manager (when used without Java)
    'gradle-kotlin': PackageManager(
        name='gradle-kotlin',
        language='kotlin',
        lock_files=[],
        config_files=['build.gradle.kts'],
        install_cmd='gradle build',
        add_cmd='gradle add dependency {package}',
        remove_cmd='gradle remove dependency {package}',
        update_cmd='gradle dependency update',
        test_cmd='gradle test',
        publish_cmd='gradle publish',
        build_cmd='gradle build',
        run_cmd='gradle run',
        version_cmd='gradle --version',
        priority=9
    ),
}


def detect_package_managers(project_path: str = ".") -> List[PackageManager]:
    """
    Detect available package managers in the given project path.
    
    Returns a list of package managers sorted by priority (highest first).
    """
    detected = []
    project_root = Path(project_path)
    
    for pm_name, pm in PACKAGE_MANAGERS.items():
        # Check for lock files (strongest indicator)
        for lock_file in pm.lock_files:
            if '*' in lock_file:
                if list(project_root.glob(lock_file)):
                    detected.append(pm)
                    break
            else:
                lock_path = project_root / lock_file
                if lock_path.exists():
                    detected.append(pm)
                    break
        
        # Check for config files if no lock files found
        if pm not in detected:
            for config_file in pm.config_files:
                if '*' in config_file:
                    if list(project_root.glob(config_file)):
                        detected.append(pm)
                        break
                else:
                    config_path = project_root / config_file
                    if config_path.exists():
                        detected.append(pm)
                        break
    
    # Sort by priority (highest first)
    detected.sort(key=lambda x: x.priority, reverse=True)
    return detected


def get_package_manager(name: str) -> Optional[PackageManager]:
    """Get a specific package manager by name."""
    return PACKAGE_MANAGERS.get(name)


def get_package_managers_by_language(language: str) -> List[PackageManager]:
    """Get all package managers for a specific language."""
    return [pm for pm in PACKAGE_MANAGERS.values() if pm.language == language]


def is_package_manager_available(pm: PackageManager) -> bool:
    """Check if a package manager is available in the system PATH."""
    return shutil.which(pm.name) is not None


def get_available_package_managers(project_path: str = ".") -> List[PackageManager]:
    """
    Get package managers that are both detected in the project and available on the system.
    """
    detected = detect_package_managers(project_path)
    available = [pm for pm in detected if is_package_manager_available(pm)]
    return available


def get_preferred_package_manager(project_path: str = ".", language: Optional[str] = None) -> Optional[PackageManager]:
    """
    Get the preferred package manager for a project.
    
    Args:
        project_path: Path to the project
        language: Optional language filter
    
    Returns:
        The highest priority available package manager, or None
    """
    available = get_available_package_managers(project_path)
    
    if language:
        available = [pm for pm in available if pm.language == language]
    
    return available[0] if available else None


def format_package_manager_command(pm: PackageManager, command_type: str, **kwargs) -> str:
    """
    Format a package manager command with the given parameters.
    
    Args:
        pm: Package manager instance
        command_type: Type of command (install, add, remove, etc.)
        **kwargs: Parameters to substitute in the command
    
    Returns:
        Formatted command string
    """
    command_template = getattr(pm, f"{command_type}_cmd", None)
    if not command_template:
        raise ValueError(f"Command type '{command_type}' not supported for {pm.name}")
    
    try:
        return command_template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required parameter {e} for command '{command_type}' in {pm.name}")


def get_package_manager_info(pm: PackageManager) -> Dict[str, Union[str, List[str]]]:
    """Get formatted information about a package manager."""
    return {
        'name': pm.name,
        'language': pm.language,
        'lock_files': pm.lock_files,
        'config_files': pm.config_files,
        'available': is_package_manager_available(pm),
        'priority': pm.priority,
        'commands': {
            'install': pm.install_cmd,
            'add': pm.add_cmd,
            'remove': pm.remove_cmd,
            'update': pm.update_cmd,
            'test': pm.test_cmd,
            'publish': pm.publish_cmd,
            'build': pm.build_cmd,
            'run': pm.run_cmd,
        }
    }


def list_all_package_managers() -> Dict[str, Dict[str, Union[str, List[str]]]]:
    """List all supported package managers with their information."""
    return {name: get_package_manager_info(pm) for name, pm in PACKAGE_MANAGERS.items()}


# Language to file extensions mapping for better detection
LANGUAGE_FILE_EXTENSIONS = {
    'python': ['.py'],
    'nodejs': ['.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs'],
    'rust': ['.rs'],
    'go': ['.go'],
    'ruby': ['.rb'],
    'php': ['.php'],
    'java': ['.java'],
    'dotnet': ['.cs', '.fs', '.vb'],
    'elixir': ['.ex', '.exs'],
    'haskell': ['.hs'],
    'swift': ['.swift'],
    'dart': ['.dart'],
    'kotlin': ['.kt', '.kts'],
}


def detect_project_language(project_path: str = ".") -> List[str]:
    """
    Detect the primary language(s) of a project based on file extensions.
    """
    project_root = Path(project_path)
    detected_languages = set()
    
    for language, extensions in LANGUAGE_FILE_EXTENSIONS.items():
        for ext in extensions:
            if list(project_root.rglob(f"*{ext}")):
                detected_languages.add(language)
                break
    
    return list(detected_languages)


def suggest_package_managers(project_path: str = ".") -> List[PackageManager]:
    """
    Suggest package managers for a project based on detected languages and available tools.
    """
    languages = detect_project_language(project_path)
    suggestions = []
    
    for language in languages:
        pms = get_package_managers_by_language(language)
        available_pms = [pm for pm in pms if is_package_manager_available(pm)]
        suggestions.extend(available_pms)
    
    # Remove duplicates and sort by priority
    unique_suggestions = list({pm.name: pm for pm in suggestions}.values())
    unique_suggestions.sort(key=lambda x: x.priority, reverse=True)
    
    return unique_suggestions
