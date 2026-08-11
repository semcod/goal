from goal.validators.dot_folders import check_dot_folders
from goal.validators.gitignore import save_gitignore


def test_env_example_is_a_versioned_safe_template(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.example").write_text("OPENROUTER_API_KEY=\n")

    assert check_dot_folders([".env.example"], config=None) == []


def test_save_gitignore_compares_complete_patterns(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("!**/secret.env.example\n")

    save_gitignore({".env.example"}, str(gitignore))

    assert gitignore.read_text().splitlines() == [
        ".env.example",
        "!**/secret.env.example",
    ]
