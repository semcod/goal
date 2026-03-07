"""Push workflow package - orchestrates the complete push/release workflow.

This package provides the complete push workflow implementation,
including commit message generation, version bumping, changelog updates,
test execution, tagging, pushing to remote, and publishing.
"""

# Core orchestrator
from .core import (
    execute_push_workflow,
    PushContext,
    show_workflow_preview,
    output_final_summary,
    run_git_local,
)

# Workflow stages
from .stages import (
    get_commit_message,
    enforce_quality_gates,
    handle_single_commit,
    handle_split_commits,
    handle_version_sync,
    get_version_info,
    handle_changelog,
    run_test_stage,
    create_tag,
    push_to_remote,
    handle_publish,
    handle_dry_run,
)

# CLI command
from .commands import push

__all__ = [
    # Core
    'execute_push_workflow',
    'PushContext',
    'show_workflow_preview',
    'output_final_summary',
    'run_git_local',
    # Stages
    'get_commit_message',
    'enforce_quality_gates',
    'handle_single_commit',
    'handle_split_commits',
    'handle_version_sync',
    'get_version_info',
    'handle_changelog',
    'run_test_stage',
    'create_tag',
    'push_to_remote',
    'handle_publish',
    'handle_dry_run',
    # CLI
    'push',
]
