# Preprompt — ticket-007

Fix only the undefined-name defect in `goal/project_bootstrap.py` and retain the
existing regression coverage in `tests/test_project_bootstrap.py`. Never print,
persist or fabricate an OpenRouter credential. Run focused and full pytest.
