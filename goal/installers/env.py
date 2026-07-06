"""Environment isolation for package-manager subprocesses.

``goal`` is almost always invoked from an *activated* virtualenv (e.g. a
monorepo-wide ``venv/`` shared across many sibling repos). Package managers
(``uv pip install``, ``pip install``) honor the ambient ``VIRTUAL_ENV``, so
without isolation they install a project's dependencies into that *outer* venv
instead of the project's own ``.venv``. The result:

* the outer venv accumulates editable installs of every project it bootstraps,
* each project's ``.venv`` stays incomplete (missing declared deps), and
* ``goal`` then runs the project's tests with ``.venv/bin/python`` and they fail
  with confusing ``ModuleNotFoundError``s.

:func:`isolated_env` returns an environment that points the package manager at
the *project's* ``.venv`` (and drops ``CONDA_PREFIX``) so installs land in the
right place regardless of what venv the user happened to have active.
"""

import os
from typing import Optional


def isolated_env(project_dir: Optional[str] = None) -> dict:
    """Return an ``os.environ`` copy scoped to the project's own ``.venv``.

    If ``<project_dir>/.venv`` exists, ``VIRTUAL_ENV`` is pointed at it and its
    ``bin`` is prepended to ``PATH``. If it does not exist yet, any ambient
    ``VIRTUAL_ENV`` is removed so an outer venv can't capture the install (uv
    creates the project ``.venv`` on ``sync``/``venv``). ``CONDA_PREFIX`` is
    always dropped so conda base environments don't interfere.
    """
    env = os.environ.copy()
    base = os.path.abspath(project_dir) if project_dir else os.getcwd()
    venv = os.path.join(base, ".venv")

    env.pop("CONDA_PREFIX", None)

    if os.path.isdir(venv):
        env["VIRTUAL_ENV"] = venv
        bin_dir = os.path.join(venv, "bin")
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
    else:
        env.pop("VIRTUAL_ENV", None)

    return env
