"""Push workflow stages - test execution."""

import sys
from typing import Dict, List, Any, Tuple

import click

from goal.cli import confirm
from goal.cli.tests import run_tests
from goal.formatter import format_push_result
from goal.io.stdio import (
    echo_auto,
    echo_status_error,
    echo_status_ok,
)


def run_test_stage(
    project_types: List[str],
    yes: bool,
    markdown: bool,
    ctx_obj: Dict[str, Any],
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: str,
) -> Tuple[str, int]:
    """Run tests with interactive or auto mode."""
    test_result = None
    test_exit_code = 0
    use_markdown = markdown or ctx_obj.get("markdown")

    if not yes:
        if confirm("Run tests?"):
            click.echo(click.style("\nRunning tests...", fg="cyan"))
            test_success = run_tests(project_types, config=ctx_obj.get("config"))
            if not test_success:
                test_exit_code = 1
                if not confirm("Tests failed. Continue anyway?", default=False):
                    if use_markdown:
                        md_output = format_push_result(
                            project_types=project_types,
                            files=files,
                            stats=stats,
                            current_version=current_version,
                            new_version=new_version,
                            commit_msg=commit_msg,
                            commit_body=commit_body,
                            test_result="Tests failed - aborted by user",
                            test_exit_code=1,
                            actions=[
                                "Detected project types",
                                "Staged changes",
                                "Attempted to run tests",
                            ],
                            error="User aborted due to test failures",
                        )
                        click.echo(md_output)
                    click.echo(click.style("Aborted.", fg="red"))
                    sys.exit(1)
        else:
            click.echo(
                click.style("  🤖 AUTO: Skipping tests (user chose N)", fg="cyan")
            )
    else:
        echo_auto("Running tests (--all mode)")
        try:
            test_success = run_tests(
                project_types,
                config=ctx_obj.get("config"),
                markdown=use_markdown,
            )
            if not test_success:
                test_exit_code = 1
                test_result = "Tests failed"
                echo_status_error("Tests failed.")
            else:
                test_exit_code = 0
                test_result = "Tests passed"
                echo_status_ok("All tests passed successfully")
        except Exception as e:
            test_exit_code = 1
            test_result = f"Test execution error: {str(e)}"
            echo_status_error(f"Error running tests: {str(e)}")

    from goal.cli.tests import get_test_execution_details
    ctx_obj["test_details"] = get_test_execution_details()

    return test_result, test_exit_code
