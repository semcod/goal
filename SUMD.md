# goal

Goal - Automated git push with enterprise-grade commit intelligence, smart conventional commit generation based on deep code analysis, and interactive release workflow management.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Intent](#intent)

## Metadata

- **name**: `goal`
- **version**: `2.1.189`
- **python_requires**: `>=3.13`
- **license**: MIT
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

## Source Map

- examples/my-new-project/src/my-new-project/__init__.py
- examples/my-new-project/tests/test_my-new-project.py
- examples/webhooks/slack-webhook.py
- examples/webhooks/discord-webhook.py
- examples/custom-hooks/post-commit.py
- examples/custom-hooks/pre-publish.py
- examples/custom-hooks/pre-commit.py
- examples/api-usage/04_version_validation.py
- examples/api-usage/05_programmatic_workflow.py
- examples/api-usage/01_basic_api.py
- examples/api-usage/03_commit_generation.py
- examples/api-usage/test_integration.py
- examples/api-usage/02_git_operations.py
- examples/validation/test_imports.py
- examples/validation/run_all_validation.py
- examples/validation/test_syntax_check.py
- examples/validation/test_readme_consistency.py
- examples/validation/test_api_signatures.py
- examples/template-generator/generate.py
- examples/testing/04_debugging_diagnostics.py
- examples/testing/03_advanced_mocking.py
- test_recovery.py
- tests/test_version_validation.py
- tests/test_file_validation.py
- tests/test_git_ops.py
- tests/test_project_bootstrap.py
- tests/test_config_shim.py
- tests/test_changelog.py
- tests/test_project_doctor.py
- tests/test_user_config.py
- tests/test_smart_commit_shim.py
- tests/test_formatter.py
- tests/test_config_validation.py
- tests/test_version_sync.py
- tests/test_cli_options.py
- tests/test_clone_repo.py
- tests/test_push_e2e.py
- .venv_test/lib/python3.13/site-packages/dotenv/version.py
- .venv_test/lib/python3.13/site-packages/dotenv/cli.py
- .venv_test/lib/python3.13/site-packages/dotenv/__init__.py
- .venv_test/lib/python3.13/site-packages/dotenv/__main__.py
- .venv_test/lib/python3.13/site-packages/dotenv/parser.py
- .venv_test/lib/python3.13/site-packages/dotenv/main.py
- .venv_test/lib/python3.13/site-packages/dotenv/variables.py
- .venv_test/lib/python3.13/site-packages/dotenv/ipython.py
- .venv_test/lib/python3.13/site-packages/referencing/exceptions.py
- .venv_test/lib/python3.13/site-packages/referencing/retrieval.py
- .venv_test/lib/python3.13/site-packages/referencing/tests/test_exceptions.py
- .venv_test/lib/python3.13/site-packages/referencing/tests/test_core.py
- .venv_test/lib/python3.13/site-packages/referencing/tests/test_referencing_suite.py
