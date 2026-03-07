"""Push command - extracted and refactored from cli.py.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.push package.
"""

# Re-export everything from the new push package for backward compatibility
try:
    from ..push import (
        push,
        execute_push_workflow,
        PushContext,
        # Workflow stages
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
        # Utilities
        show_workflow_preview,
        output_final_summary,
    )
except ImportError:
    # Fallback if relative imports fail
    from goal.push import (
        push,
        execute_push_workflow,
        PushContext,
        # Workflow stages
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
        # Utilities
        show_workflow_preview,
        output_final_summary,
    )


# Maintain backward compatibility for direct function access
__all__ = [
    'push',
    'execute_push_workflow',
    'PushContext',
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
    'show_workflow_preview',
    'output_final_summary',
]
