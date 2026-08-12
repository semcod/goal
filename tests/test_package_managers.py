"""Regression tests for built-in package publication commands."""

import pytest

from goal.config.constants import DEFAULT_CONFIG
from goal.package_managers import PACKAGE_MANAGERS


def test_default_python_publish_command_is_retry_safe():
    assert DEFAULT_CONFIG["strategies"]["python"]["publish"] == (
        "twine upload --skip-existing dist/{project_name}-{version}*"
    )


@pytest.mark.parametrize(
    ("manager", "expected"),
    [
        ("pip", "python -m twine upload --skip-existing dist/*"),
        (
            "pipenv",
            "pipenv run python -m twine upload --skip-existing dist/*",
        ),
    ],
)
def test_twine_package_manager_publish_commands_are_retry_safe(manager, expected):
    assert PACKAGE_MANAGERS[manager].publish_cmd == expected
